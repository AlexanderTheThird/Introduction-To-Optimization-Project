import pulp as pl
import pandas as pd
import os

# Data from the Spreadsheet

tas = ["A", "B", "C", "D", "E", "F", "G", "H"]

courses = ["C00", "C01", "C02", "C03", "C04", "I1", "C05"]

# Remaining marking load in hours
remaining_load = {
    "C00": 31,
    "C01": 68.333,
    "C02": 46.333,
    "C03": 38.667,
    "C04": 176,
    "I1": 8.667,
    "C05": 85
}

# Eligibility matrix
# 0 = cannot mark
# 1 = assigned TA, normal pay
# 2 = secondary marker, 1.3x pay
eligibility = {
    "A": {"C00": 2, "C01": 1, "C02": 2, "C03": 1, "C04": 0, "I1": 0, "C05": 2},
    "B": {"C00": 2, "C01": 1, "C02": 2, "C03": 2, "C04": 0, "I1": 0, "C05": 2},
    "C": {"C00": 2, "C01": 2, "C02": 1, "C03": 0, "C04": 0, "I1": 2, "C05": 0},
    "D": {"C00": 2, "C01": 2, "C02": 0, "C03": 0, "C04": 0, "I1": 2, "C05": 1},
    "E": {"C00": 1, "C01": 2, "C02": 2, "C03": 0, "C04": 2, "I1": 1, "C05": 2},
    "F": {"C00": 2, "C01": 2, "C02": 0, "C03": 0, "C04": 2, "I1": 2, "C05": 2},
    "G": {"C00": 2, "C01": 2, "C02": 0, "C03": 0, "C04": 2, "I1": 2, "C05": 2},
    "H": {"C00": 2, "C01": 2, "C02": 0, "C03": 2, "C04": 0, "I1": 2, "C05": 2}
}

# Weights to Experiment With.
weight_scenarios = [
    {
        "experiment": "experiment_1_balanced",
        "w1": 0.50,
        "w2": 0.50,
        "description": "Balanced demand and fairness with moderate cost concern"
    },
    {
        "experiment": "experiment_2_fairness_focused",
        "w1": 0.6,
        "w2": 0.4,
        "description": "Greater emphasis on fairness"
    },
    {
        "experiment": "experiment_3_strong_fairness_low_cost",
        "w1": 0.75,
        "w2": 0.25,
        "description": "Strong fairness emphasis with low cost concern"
    }
]

# Helper Functions
def pay_rate(code):
    if code == 1:
        return 1.0
    elif code == 2:
        return 1.3
    return 0

def marker_type(code):
    if code == 1:
        return "Assigned TA"
    elif code == 2:
        return "Secondary marker"
    return "Not eligible"

# Output Directory
output_dir = "experiment_outputs"
os.makedirs(output_dir, exist_ok=True)

# Basic Calculations
total_remaining_load = sum(remaining_load.values())
average_load = total_remaining_load / len(tas)

base_cost = total_remaining_load
max_extra_cost = 0.3 * total_remaining_load

# -----------------------------
# FUNCTION TO BUILD AND SOLVE MODEL
# -----------------------------

def solve_experiment(experiment_name, w1, w2, description):
    model = pl.LpProblem(f"TA_Normalized_GP_{experiment_name}", pl.LpMinimize)

    # Decision variables
    x = pl.LpVariable.dicts(
        "x",
        [(i, j) for i in tas for j in courses],
        lowBound=0,
        cat="Continuous"
    )

    # Fairness deviation variables
    f_above = pl.LpVariable.dicts("fair_above_average", tas, lowBound=0)
    f_below = pl.LpVariable.dicts("fair_below_average", tas, lowBound=0)

    # Constraints
    # Meet remaining course demand
    for j in courses:
        model += (
    pl.lpSum(x[i, j] for i in tas if eligibility[i][j] > 0)
    == remaining_load[j]
), f"Demand_Balance_{j}"

    # Eligibility constraint
    for i in tas:
        for j in courses:
            if eligibility[i][j] == 0:
                model += x[i, j] == 0, f"Eligibility_{i}_{j}"

    # Goal 1: Fairness around average workload
    for i in tas:
        total_load_i = pl.lpSum(x[i, j] for j in courses)

        model += (
            total_load_i - average_load
            == f_above[i] - f_below[i]
        ), f"Fairness_Balance_{i}"

    fairness_deviation = pl.lpSum(
        f_above[i] + f_below[i]
        for i in tas
    )

    total_pay_cost = pl.lpSum(
        x[i, j] * pay_rate(eligibility[i][j])
        for i in tas
        for j in courses
        if eligibility[i][j] > 0
    )

    extra_pay_cost = total_pay_cost - base_cost

    # Normalized objective components
    G1 = fairness_deviation / total_remaining_load
    G2 = extra_pay_cost / max_extra_cost

    model += (
        w1 * G1
        + w2 * G2
    ), "Normalized_Weighted_Goal_Objective"

    # Model Solving.
    model.solve(pl.PULP_CBC_CMD(msg=False))

    status = pl.LpStatus[model.status]
    objective_value = pl.value(model.objective)

    # Assignment Details
    assignment_rows = []

    for i in tas:
        for j in courses:
            hours = x[i, j].varValue or 0

            if hours > 0.001:
                assignment_rows.append({
                    "Experiment": experiment_name,
                    "TA": i,
                    "Course": j,
                    "Hours Assigned": round(hours, 3),
                    "Eligibility Code": eligibility[i][j],
                    "Marker Type": marker_type(eligibility[i][j]),
                    "Pay Rate": pay_rate(eligibility[i][j]),
                    "Relative Cost": round(hours * pay_rate(eligibility[i][j]), 3)
                })

    df_assignment = pd.DataFrame(assignment_rows)

    # Workload Summary
    workload_rows = []

    for i in tas:
        total_hours = sum((x[i, j].varValue or 0) for j in courses)

        assigned_hours = sum(
            (x[i, j].varValue or 0)
            for j in courses
            if eligibility[i][j] == 1
        )

        secondary_hours = sum(
            (x[i, j].varValue or 0)
            for j in courses
            if eligibility[i][j] == 2
        )

        total_cost = sum(
            (x[i, j].varValue or 0) * pay_rate(eligibility[i][j])
            for j in courses
            if eligibility[i][j] > 0
        )

        workload_rows.append({
            "Experiment": experiment_name,
            "TA": i,
            "Total Hours": round(total_hours, 3),
            "Assigned TA Hours": round(assigned_hours, 3),
            "Secondary Marker Hours": round(secondary_hours, 3),
            "Average Target": round(average_load, 3),
            "Deviation from Average": round(abs(total_hours - average_load), 3),
            "Fair Above Average": round(f_above[i].varValue or 0, 3),
            "Fair Below Average": round(f_below[i].varValue or 0, 3),
            "Relative Pay Cost": round(total_cost, 3)
        })

    df_workload = pd.DataFrame(workload_rows)

    # Course Fulfillment Summary
    course_rows = []

    for j in courses:
        assigned = sum(
            (x[i, j].varValue or 0)
            for i in tas
            if eligibility[i][j] > 0
        )

        course_rows.append({
    "Experiment": experiment_name,
    "Course": j,
    "Required Remaining Load": round(remaining_load[j], 3),
    "Assigned Hours": round(assigned, 3),
    "Difference": round(assigned - remaining_load[j], 3)
})

    df_courses = pd.DataFrame(course_rows)

    # Objective Summary
    total_secondary_hours = df_workload["Secondary Marker Hours"].sum()
    total_assigned_hours = df_workload["Total Hours"].sum()

    objective_summary = {
        "Experiment": experiment_name,
        "Description": description,
        "Status": status,
        "w1_Fairness": w1,
        "w2_Cost": w2,
        "Objective Value": round(objective_value, 6),
        "G1 Fairness Deviation Normalized": round(pl.value(G1), 6),
        "G2 Extra Cost Normalized": round(pl.value(G2), 6),
        "Fairness Deviation Raw": round(pl.value(fairness_deviation), 3),
        "Total Pay Cost": round(pl.value(total_pay_cost), 3),
        "Extra Pay Cost": round(pl.value(extra_pay_cost), 3),
        "Total Remaining Load": round(total_remaining_load, 3),
        "Total Assigned Hours": round(total_assigned_hours, 3),
        "Average Load Per TA": round(average_load, 3),
        "Total Secondary Marker Hours": round(total_secondary_hours, 3),
        "Min TA Workload": round(df_workload["Total Hours"].min(), 3),
        "Max TA Workload": round(df_workload["Total Hours"].max(), 3),
        "Workload Range": round(df_workload["Total Hours"].max() - df_workload["Total Hours"].min(), 3)
    }

    df_objective = pd.DataFrame([objective_summary])

    # CSV File Generation
    experiment_folder = os.path.join(output_dir, experiment_name)
    os.makedirs(experiment_folder, exist_ok=True)

    df_assignment.to_csv(
        os.path.join(experiment_folder, "assignment_details.csv"),
        index=False
    )

    df_workload.to_csv(
        os.path.join(experiment_folder, "ta_workload_summary.csv"),
        index=False
    )

    df_courses.to_csv(
        os.path.join(experiment_folder, "course_fulfillment_summary.csv"),
        index=False
    )

    df_objective.to_csv(
        os.path.join(experiment_folder, "objective_summary.csv"),
        index=False
    )

    return df_assignment, df_workload, df_courses, df_objective


# Experiment Running
all_assignment_results = []
all_workload_results = []
all_course_results = []
all_objective_results = []

for scenario in weight_scenarios:
    print(f"\nRunning {scenario['experiment']}...")

    df_assignment, df_workload, df_courses, df_objective = solve_experiment(
        experiment_name=scenario["experiment"],
        w1=scenario["w1"],
        w2=scenario["w2"],
        description=scenario["description"]
    )

    all_assignment_results.append(df_assignment)
    all_workload_results.append(df_workload)
    all_course_results.append(df_courses)
    all_objective_results.append(df_objective)

    print("Status:", df_objective.loc[0, "Status"])
    print("Objective Value:", df_objective.loc[0, "Objective Value"])
    print("Fairness Deviation:", df_objective.loc[0, "Fairness Deviation Raw"])
    print("Total Pay Cost:", df_objective.loc[0, "Total Pay Cost"])
    print("Workload Range:", df_objective.loc[0, "Workload Range"])

# Combination of CSV Files
df_all_assignments = pd.concat(all_assignment_results, ignore_index=True)
df_all_workloads = pd.concat(all_workload_results, ignore_index=True)
df_all_courses = pd.concat(all_course_results, ignore_index=True)
df_all_objectives = pd.concat(all_objective_results, ignore_index=True)

df_all_assignments.to_csv(
    os.path.join(output_dir, "all_experiments_assignment_details.csv"),
    index=False
)

df_all_workloads.to_csv(
    os.path.join(output_dir, "all_experiments_ta_workload_summary.csv"),
    index=False
)

df_all_courses.to_csv(
    os.path.join(output_dir, "all_experiments_course_fulfillment_summary.csv"),
    index=False
)

df_all_objectives.to_csv(
    os.path.join(output_dir, "all_experiments_objective_summary.csv"),
    index=False
)

# Final Comparison.
print("\n==============================")
print("FINAL EXPERIMENT COMPARISON")
print("==============================")

comparison_columns = [
    "Experiment",
    "w1_Fairness",
    "w2_Cost",
    "Objective Value",
    "G1 Fairness Deviation Normalized",
    "G2 Extra Cost Normalized",
    "Fairness Deviation Raw",
    "Total Pay Cost",
    "Extra Pay Cost",
    "Total Secondary Marker Hours",
    "Workload Range"
]

print(df_all_objectives[comparison_columns].to_string(index=False))

print("\nCSV files saved in folder:", output_dir)

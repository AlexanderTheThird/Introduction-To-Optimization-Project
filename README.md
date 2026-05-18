# Introduction-To-Optimization-Project
## Author
Joshua Hannays, 500001534; UWI Five Islands

## Academic Integrity Statement

This repository was created as part of a university optimization course project. The code and report are intended to demonstrate the formulation, implementation, and interpretation of a Goal Programming model for TA marking workload allocation.

## Project Overview

This project presents a Goal Programming optimization model for fairly distributing the remaining final examination marking workload among Teaching Assistants (TAs). The problem arises when different courses have different class sizes and marking requirements, causing some TAs to receive significantly more marking work than others.

The model assigns remaining marking hours to eligible TAs while balancing three main goals:

1. Meet the remaining marking demand for each course.
2. Minimize deviation from the average TA workload.
3. Minimize total relative compensation cost, where secondary markers are paid at 1.3 times the normal rate.

The model is implemented in Python using the PuLP optimization library.

---

## Problem Context

The department has a set of courses requiring final exam marking support. Each course has a remaining marking load measured in hours. A group of TAs is available to help with marking, but not every TA is eligible to mark every course.

Eligibility is represented using the following coding system:

| Code | Meaning |
|---:|---|
| 0 | TA cannot mark the course |
| 1 | TA is an assigned/primary marker and receives normal pay |
| 2 | TA is a secondary marker and receives 1.3 times the normal pay rate |

The aim is to allocate marking hours fairly while ensuring that all remaining course marking demand is satisfied.

---

## Dataset

The dataset was derived from the course spreadsheet provided for the project.

The main data used by the model includes:

- Course list
- Remaining marking load for each course
- TA list
- TA-course eligibility matrix
- Pay multiplier for assigned and secondary markers

### Remaining Course Loads

| Course | Remaining Load (Hours) |
|---|---:|
| C00 | 31.000 |
| C01 | 68.333 |
| C02 | 46.333 |
| C03 | 38.667 |
| C04 | 176.000 |
| I1 | 8.667 |
| C05 | 85.000 |

Total remaining load:

```text
454 hours
```

## Mathematical Model Summary

The full mathematical formulation is provided in the project report. In summary, the model uses Goal Programming to assign remaining marking hours to eligible TAs.

The model has wo goals:

1. Minimize deviation from the average TA workload.
2. Minimize total relative pay cost, where secondary markers are paid at 1.3 times the normal rate.

The main decision variable is:

x[i,j] = number of marking hours assigned to TA i for course j

## Limitations

The main limitations of the model are:

1. The spreadsheet does not provide individual TA availability limits.
2. The model assumes the 1.3 rate represents a pay multiplier, not a marking speed multiplier.
3. Marking hours are treated as divisible continuous values.
4. The model does not consider TA preferences, scheduling conflicts, or marking quality.
5. Fairness is measured only by deviation from average workload.

A fuller discussion of these limitations is provided in the project report.

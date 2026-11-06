# Auspify EMS — Text wireframes

These wireframes were written before the React implementation. They describe
the layout and information hierarchy of every screen; the final UI follows
them with a responsive CSS design system.

## Shared navbar

```text
┌──────────────────────────────────────────────────────────────────────┐
│ [A] Auspify EMS              Dashboard  Employees  Departments  Reports│
│     Employee Management                                              │
└──────────────────────────────────────────────────────────────────────┘
```

On screens narrower than 760px the links collapse into a hamburger menu.

## 1. Dashboard (`/`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Overview / Dashboard                       [View reports] [Add employee]│
├───────────────┬───────────────┬───────────────┬──────────────────────┤
│ Total employees│ Active       │ On leave      │ Total payroll        │
│ 25            │ 21           │ 4             │ GH₵1,950,000         │
│ Across 5 dept.│ Currently... │ Temporary...  │ GH₵78,000 average    │
├───────────────┴───────────────┴───────────────┴──────────────────────┤
│ Headcount by department (bar chart)   │ Status breakdown (pie chart) │
│                                       │                              │
├───────────────────────────────────────┴──────────────────────────────┤
│ Recent hires                                    [View all employees] │
│ Employee | Department | Status | Hire date                           │
│ [AO] Abena Osei | Marketing | Active | 13 May 2024                   │
└──────────────────────────────────────────────────────────────────────┘
```

## 2. Employee list (`/employees`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ People / Employees                                  [Add employee]   │
├──────────────────────────────────────────────────────────────────────┤
│ [⌕ Search by name, email, or employee code…]  [x] Show terminated  [Clear] │
│ Department [All departments] Status [All statuses] Job title [    ]  │
│ Hired from [        ] Hired to [        ] Sort by [Last name] Order [Asc] │
│ Per page [10]                                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Showing 1–10 of 25 employees                 [< Previous] Page 1 of 3 [Next >] │
├──────────────────────────────────────────────────────────────────────┤
│ Employee | Job title | Department | Status | Salary | Hire date | Actions │
│ [KA] Kwame Mensah | Engineering Manager | Engineering | Active | GH₵145,000 | 01 Feb 2018 | View Edit Terminate Delete │
│ ...                                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

Filters are applied live. Search is debounced by 300 ms. Terminated
employees are hidden unless **Show terminated** is checked or the status
filter is set to Terminated.

## 3. Employee form (`/employees/new`, `/employees/:id/edit`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ← Back                                                               │
│ Add employee                                                         │
│ Register a new employee. Fields marked * are required.               │
├──────────────────────────────────────────────────────────────────────┤
│ Personal details                                                     │
│ First name* [        ]  Last name* [        ]                        │
│ Email* [              ]  Phone [              ]                      │
│ Date of birth [        ]  Gender [Not specified ▾]                   │
│ Address [textarea                                                   ] │
├──────────────────────────────────────────────────────────────────────┤
│ Employment details                                                   │
│ Employee code [Auto-generated]  Job title* [        ]                │
│ Department* [Select a department ▾]  Salary (GHS)* [        ]       │
│ Hire date* [        ]  Status [Active ▾]                             │
├──────────────────────────────────────────────────────────────────────┤
│                                          [Cancel] [Register employee]│
└──────────────────────────────────────────────────────────────────────┘
```

Client-side validation highlights invalid fields. Server errors appear in a
banner and, where possible, next to the relevant field.

## 4. Employee details (`/employees/:id`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ← Back to employees                                                  │
│ [KM] Kwame Mensah  [Active]        [Edit] [Terminate] [Delete permanently] │
│      Engineering Manager · Engineering                               │
├──────────────────────────────────────────────────────────────────────┤
│ Employee record                                      [EMP-0001]      │
│ Email            │ Phone             │ Department   │ Job title       │
│ Salary           │ Hire date         │ Date of birth│ Gender          │
│ Address (full width)                                                 │
│ Created          │ Last updated                                        │
└──────────────────────────────────────────────────────────────────────┘
```

Terminate and Delete permanently both open a confirmation dialog.

## 5. Departments (`/departments`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Organisation / Departments                       [Add department]    │
├──────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────┐  ┌────────────────────────┐               │
│ │ Engineering            │  │ Finance                │               │
│ │ Manager: Kwame Mensah  │  │ Manager: Kofi Asante   │               │
│ │ 5 employees            │  │ 5 employees            │               │
│ │ Builds and maintains…  │  │ Budgeting, accounting… │               │
│ │ 5 active  0 inactive   │  │ 5 active  0 inactive   │               │
│ │ [Edit] [Delete]        │  │ [Edit] [Delete]        │               │
│ └────────────────────────┘  └────────────────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
```

**Add/Edit department modal**

```text
┌──────────────────────────────────────────────────────────┐
│ Add department                                       ×   │
│ Name * [                    ]                            │
│ Description [textarea                                  ] │
│ Manager [Unassigned ▾]                                  │
│                              [Cancel] [Create department]│
└──────────────────────────────────────────────────────────┘
```

## 6. Reports (`/reports`)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Insights / Reports       [Export headcount CSV] [Export directory CSV]│
├───────────────┬───────────────┬───────────────┬──────────────────────┤
│ Total employees│ Total payroll│ Average salary│ New hires           │
├───────────────┴───────────────┴───────────────┴──────────────────────┤
│ Headcount by department (bar)         │ Status breakdown (pie)       │
├───────────────────────────────────────┴──────────────────────────────┤
│ Salary summary                        [Export salary CSV]            │
│ Department | Employees | Minimum | Maximum | Average | Total         │
├──────────────────────────────────────────────────────────────────────┤
│ New hires                       [From] [To] [Apply]                  │
│ Employee | Department | Status | Hire date                           │
└──────────────────────────────────────────────────────────────────────┘
```

## 7. Confirmation dialog (shared)

```text
┌──────────────────────────────────────────────┐
│ Delete employee permanently?                 │
│ This will permanently remove Kwame Mensah    │
│ from the database. This action cannot be     │
│ undone.                                      │
│                        [Cancel] [Delete permanently] │
└──────────────────────────────────────────────┘
```

## 8. Notification toast (shared)

```text
┌────────────────────────────────────────────────┐
│ ✓ Employee registered successfully.          × │
└────────────────────────────────────────────────┘
```

Toasts appear in the bottom-right corner, auto-dismiss after 4.5 seconds, and
use success, error, or info styling.

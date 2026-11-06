"""Server-side validation for employees and departments.

Validation is deliberately kept in one place so the API returns consistent
field errors and the tests can exercise every rule without HTTP noise.
"""

from datetime import date, datetime

STATUSES = ("active", "on_leave", "terminated")
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_JOB_TITLE_LENGTH = 150
MAX_PHONE_LENGTH = 40
MAX_ADDRESS_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 500


def clean_string(value):
    """Return a trimmed string, or None for empty/non-string values."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def is_valid_date(value) -> bool:
    """True when `value` is a real date in YYYY-MM-DD form."""
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_date(value):
    """Parse a YYYY-MM-DD string into a date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def validate_employee(payload, existing=None):
    """Validate an employee payload.

    Returns `(data, errors)` where `errors` maps field names to messages.
    `existing` is the current row for updates; it is used to keep the
    employee code when the client omits it.
    """
    if not isinstance(payload, dict):
        return None, {"form": "Request body must be a JSON object."}

    errors = {}
    data = {}

    # Required text fields -------------------------------------------------
    first_name = clean_string(payload.get("first_name"))
    if not first_name:
        errors["first_name"] = "First name is required."
    elif len(first_name) > MAX_NAME_LENGTH:
        errors["first_name"] = f"First name must be at most {MAX_NAME_LENGTH} characters."
    else:
        data["first_name"] = first_name

    last_name = clean_string(payload.get("last_name"))
    if not last_name:
        errors["last_name"] = "Last name is required."
    elif len(last_name) > MAX_NAME_LENGTH:
        errors["last_name"] = f"Last name must be at most {MAX_NAME_LENGTH} characters."
    else:
        data["last_name"] = last_name

    email = clean_string(payload.get("email"))
    if not email:
        errors["email"] = "Email is required."
    elif len(email) > MAX_EMAIL_LENGTH:
        errors["email"] = f"Email must be at most {MAX_EMAIL_LENGTH} characters."
    elif not _looks_like_email(email):
        errors["email"] = "Enter a valid email address."
    else:
        data["email"] = email.lower()

    job_title = clean_string(payload.get("job_title"))
    if not job_title:
        errors["job_title"] = "Job title is required."
    elif len(job_title) > MAX_JOB_TITLE_LENGTH:
        errors["job_title"] = f"Job title must be at most {MAX_JOB_TITLE_LENGTH} characters."
    else:
        data["job_title"] = job_title

    # Employee code (optional on create, kept on update) -------------------
    raw_code = payload.get("employee_code")
    if raw_code is not None and clean_string(raw_code) is None:
        errors["employee_code"] = "Employee code cannot be blank."
    else:
        code = clean_string(raw_code)
        if code:
            if len(code) > 20:
                errors["employee_code"] = "Employee code must be at most 20 characters."
            elif not code.replace("-", "").replace("_", "").isalnum():
                errors["employee_code"] = (
                    "Employee code may only contain letters, numbers, hyphens, and underscores."
                )
            else:
                data["employee_code"] = code
        elif existing:
            data["employee_code"] = existing["employee_code"]

    # Department -----------------------------------------------------------
    department_id = payload.get("department_id")
    if department_id is None or department_id == "":
        errors["department_id"] = "Department is required."
    else:
        try:
            department_id = int(department_id)
        except (TypeError, ValueError):
            errors["department_id"] = "Department must be a valid ID."
        else:
            if department_id <= 0:
                errors["department_id"] = "Department must be a valid ID."
            else:
                data["department_id"] = department_id

    # Hire date ------------------------------------------------------------
    hire_date = clean_string(payload.get("hire_date"))
    if not hire_date:
        errors["hire_date"] = "Hire date is required."
    elif not is_valid_date(hire_date):
        errors["hire_date"] = "Hire date must use the YYYY-MM-DD format."
    elif parse_date(hire_date) > date.today():
        errors["hire_date"] = "Hire date cannot be in the future."
    else:
        data["hire_date"] = hire_date

    # Date of birth (optional) --------------------------------------------
    dob = clean_string(payload.get("date_of_birth"))
    if dob:
        if not is_valid_date(dob):
            errors["date_of_birth"] = "Date of birth must use the YYYY-MM-DD format."
        elif parse_date(dob) > date.today():
            errors["date_of_birth"] = "Date of birth cannot be in the future."
        elif parse_date(dob).year < 1900:
            errors["date_of_birth"] = "Date of birth must be after 1900."
        else:
            data["date_of_birth"] = dob
    else:
        data["date_of_birth"] = None

    # Salary ---------------------------------------------------------------
    salary = payload.get("salary", 0)
    if salary is None or salary == "":
        salary = 0
    try:
        salary = float(salary)
    except (TypeError, ValueError):
        errors["salary"] = "Salary must be a number."
    else:
        if salary < 0:
            errors["salary"] = "Salary cannot be negative."
        elif salary > 1_000_000_000:
            errors["salary"] = "Salary is unrealistically large."
        else:
            data["salary"] = salary

    # Status ---------------------------------------------------------------
    status = clean_string(payload.get("status")) or "active"
    if status not in STATUSES:
        errors["status"] = "Status must be active, on_leave, or terminated."
    else:
        data["status"] = status

    # Optional text fields -------------------------------------------------
    phone = clean_string(payload.get("phone"))
    if phone and len(phone) > MAX_PHONE_LENGTH:
        errors["phone"] = f"Phone must be at most {MAX_PHONE_LENGTH} characters."
    else:
        data["phone"] = phone

    gender = clean_string(payload.get("gender"))
    if gender and len(gender) > 30:
        errors["gender"] = "Gender must be at most 30 characters."
    else:
        data["gender"] = gender

    address = clean_string(payload.get("address"))
    if address and len(address) > MAX_ADDRESS_LENGTH:
        errors["address"] = f"Address must be at most {MAX_ADDRESS_LENGTH} characters."
    else:
        data["address"] = address

    return data, errors


def validate_department(payload, existing=None):
    """Validate a department payload. Returns `(data, errors)`."""
    if not isinstance(payload, dict):
        return None, {"form": "Request body must be a JSON object."}

    errors = {}
    data = {}

    name = clean_string(payload.get("name"))
    if not name:
        errors["name"] = "Department name is required."
    elif len(name) < 2:
        errors["name"] = "Department name must be at least 2 characters."
    elif len(name) > MAX_NAME_LENGTH:
        errors["name"] = f"Department name must be at most {MAX_NAME_LENGTH} characters."
    else:
        data["name"] = name

    description = clean_string(payload.get("description"))
    if description and len(description) > MAX_DESCRIPTION_LENGTH:
        errors["description"] = (
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )
    else:
        data["description"] = description

    manager_id = payload.get("manager_id")
    if manager_id is None or manager_id == "":
        data["manager_id"] = None
    else:
        try:
            manager_id = int(manager_id)
        except (TypeError, ValueError):
            errors["manager_id"] = "Manager must be a valid employee ID."
        else:
            if manager_id <= 0:
                errors["manager_id"] = "Manager must be a valid employee ID."
            else:
                data["manager_id"] = manager_id

    return data, errors


def _looks_like_email(value):
    """A pragmatic email check: one @, a dot in the domain, no spaces."""
    if " " in value or value.count("@") != 1:
        return False
    local, _, domain = value.partition("@")
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False
    return True

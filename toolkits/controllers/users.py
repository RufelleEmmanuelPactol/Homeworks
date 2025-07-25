from toolkits.db import run_query
from st_pages import Page, add_page_title, Section




def get_users(emails):
    if not emails:
        return
    strformat = '('
    for email in emails:
        strformat += f'"{email}",'
    strformat = strformat[:-1]
    strformat += ')'
    return run_query(f"SELECT * FROM users where email in {strformat}")


def get_classes(user):
    return run_query(f"SELECT * FROM hackathon_2025_instructor_classes where user_id = {user.id}")

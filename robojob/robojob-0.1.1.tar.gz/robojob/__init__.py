from robojob.job import JobExecution

def go(job_name) -> JobExecution:
    return JobExecution(job_name)

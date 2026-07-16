"""Skill sys.datetime — current local date & time."""
import datetime


def run(inputs, ctx):
    return {"now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

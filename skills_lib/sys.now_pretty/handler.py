"""Skill sys.now_pretty — human-readable Polish date/time."""
import datetime


def run(inputs, ctx):
    dni = ["poniedzialek", "wtorek", "sroda", "czwartek", "piatek", "sobota", "niedziela"]
    mies = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
            "lipca", "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"]
    n = datetime.datetime.now()
    pretty = f"{dni[n.weekday()]}, {n.day} {mies[n.month - 1]} {n.year}, {n:%H:%M}"
    return {"ok": True, "pretty": pretty}

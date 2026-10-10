from __future__ import annotations
from .catalog import QUESTION_BY_ID, ACTION_META

PRIORITY = {"P0":0,"P1":1,"P2":2,"P3":3,"P4":4}
STATE_RANK = {"UNKNOWN_OR_NOT_PREPARED":0,"PARTIAL":1,"CONFIRMED":9}

P0_QUESTIONS = {"AWR_Q10_CARE","AWR_Q11_DIGITAL_FAMILY_INFO","AWR_Q12_WELLDYING_CONVERSATION"}
FOUNDATIONAL = {"AWR_Q01_RETIREMENT_AGE","AWR_Q02_NPS","AWR_Q04_RETIREMENT_BUDGET","AWR_Q06_ASSETS_DEBT"}

INCOME_GAP_PREREQUISITES = {
    "AWR_Q01_RETIREMENT_AGE",
    "AWR_Q02_NPS",
    "AWR_Q04_RETIREMENT_BUDGET",
}

def select_top3(answers: dict[str,str]) -> list[dict]:
    unresolved = []
    for qid, state in answers.items():
        if state == "CONFIRMED":
            continue
        if qid == "AWR_Q05_INCOME_GAP":
            ready = all(answers.get(x) == "CONFIRMED" for x in INCOME_GAP_PREREQUISITES)
            if not ready:
                continue
        q = QUESTION_BY_ID[qid]
        action = q["action"]
        title, default_class, stable = ACTION_META[action]
        pclass = default_class
        if qid in P0_QUESTIONS and state == "UNKNOWN_OR_NOT_PREPARED":
            pclass = "P0"
        elif qid in FOUNDATIONAL:
            pclass = "P1"
        unresolved.append({
            "question_id": qid,
            "action_catalog_id": action,
            "title": title,
            "mode": "VERIFY" if state == "PARTIAL" else "CREATE",
            "priority_class": pclass,
            "reason_code": f"{qid}:{state}",
            "_state": state,
            "_stable": stable,
        })

    p0 = sorted((x for x in unresolved if x["priority_class"] == "P0"), key=lambda x:(STATE_RANK[x["_state"]],x["_stable"]))[:1]
    p0_ids = {x["action_catalog_id"] for x in p0}
    rest = [x for x in unresolved if x["action_catalog_id"] not in p0_ids]
    for x in rest:
        if x["priority_class"] == "P0":
            x["priority_class"] = ACTION_META[x["action_catalog_id"]][1]
    rest.sort(key=lambda x:(PRIORITY[x["priority_class"]],STATE_RANK[x["_state"]],x["_stable"]))
    selected = (p0 + rest)[:3]
    for x in selected:
        x.pop("_state", None)
        x.pop("_stable", None)
    return selected

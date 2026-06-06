def classify_candidate(state):

    resume = state["resume_text"].lower()

    if "10 years" in resume:
        level = "senior"
    elif "5 years" in resume:
        level = "mid"
    else:
        level = "junior"

    print(f"Candidate Level: {level}")

    state["seniority"] = level

    return state
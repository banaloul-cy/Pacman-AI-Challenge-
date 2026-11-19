
"""
Test the competition winner rules.

Priority:
1. Level completion
2. Higher score
3. Shorter time
4. Tie
"""


def calculate_winner(human, ai):

    if human["completed"] != ai["completed"]:
        return "HUMAN" if human["completed"] else "AI"

    if human["score"] != ai["score"]:
        return (
            "HUMAN"
            if human["score"] > ai["score"]
            else "AI"
        )

    if abs(human["time"] - ai["time"]) > 0.001:
        return (
            "HUMAN"
            if human["time"] < ai["time"]
            else "AI"
        )

    return "TIE"


def result(completed, score, time):
    return {
        "completed": completed,
        "score": score,
        "time": time
    }


tests = [
    (
        "AI completes, human does not",
        result(False, 2000, 20),
        result(True, 1000, 60),
        "AI"
    ),
    (
        "Human completes, AI does not",
        result(True, 1000, 60),
        result(False, 2000, 20),
        "HUMAN"
    ),
    (
        "Higher score wins",
        result(True, 1500, 70),
        result(True, 1400, 50),
        "HUMAN"
    ),
    (
        "Shorter time wins",
        result(True, 1500, 50),
        result(True, 1500, 60),
        "HUMAN"
    ),
    (
        "Identical results produce a tie",
        result(True, 1500, 60),
        result(True, 1500, 60),
        "TIE"
    ),
    (
        "AI wins by score",
        result(False, 500, 20),
        result(False, 700, 30),
        "AI"
    )
]


passed = 0

for name, human, ai, expected in tests:

    actual = calculate_winner(human, ai)

    if actual == expected:
        print(f"PASS - {name}")
        passed += 1
    else:
        print(
            f"FAIL - {name}: "
            f"expected {expected}, got {actual}"
        )


print()
print(f"RESULT: {passed}/{len(tests)} tests passed")

if passed == len(tests):
    print("WINNER LOGIC TESTS PASSED!")
else:
    print("WINNER LOGIC TESTS FAILED!")

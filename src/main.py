from src.leetcode_agent import LeetCodeThinkingAgent


def main():
    agent = LeetCodeThinkingAgent()

    daily_count = int(input("How many problems would you like to solve today? "))
    problems = agent.get_daily_problems(daily_count)

    for problem in problems:
        print(f"\nProblem: {problem.title}")
        print(f"Description: {problem.description}")

        iterations = 0
        pseudocode_approved = False

        while not pseudocode_approved:
            iterations += 1
            pseudocode = input("\nEnter your pseudocode solution: ")
            analysis = agent.analyze_pseudocode(problem, pseudocode)
            print(f"\nAnalysis: {analysis}")

            if "solid" in analysis:
                pseudocode_approved = True
            else:
                if input("\nRefine your pseudocode? (y/n): ").lower() != "y":
                    break

        walkthrough = input("\nWalk through your solution with examples: ")
        verification = agent.verify_walkthrough(problem, walkthrough)
        print(f"\nVerification: {verification}")

        agent.record_attempt(problem.id, iterations)


if __name__ == "__main__":
    main()

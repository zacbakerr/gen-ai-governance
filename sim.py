import random
import argparse
import time
import openai
from collections import defaultdict
import json

class Senator:
  def __init__(self, name, party, state, experience, traits, policies, backend='gpt-4'):
    self.name = name
    self.party = party
    self.state = state
    self.experience = experience
    self.traits = traits
    self.policies = policies
    self.backend = backend
    self.agent_hist = ""
    self.memory = defaultdict(list)

  def inference_senator(self, context, question):
    # Enhanced the response generation to focus more on persona and issue passion
    prompt = self.system_prompt() + "\n" + context + "\nSenator's view: " + question
    if self.backend == "gpt-4":
        response = openai.ChatCompletion.create(
            model="gpt-4",
             messages=[
                 {"role": "system", "content": prompt},
                 {"role": "user", "content": question},
             ],
             temperature=0.7,
        )
        answer = response["choices"][0]["message"]["content"]
    else:
        raise Exception("No model by the name {}".format(self.backend))
        
    self.agent_hist += question + "\n\n" + answer + "\n\n"
    self.memory[context].append(answer)  # Storing the response in memory
    return answer

  def system_prompt(self):
        # Revised to emphasize the senator's active engagement and depth of their stance on issues
    policy_focus = ', '.join(f"{policy}" for policy in self.policies)
    return f"Senator {self.name} from {self.state} represents the {self.party} with {self.experience} years in the Senate. Known for being {', '.join(self.traits)}. Focused on policies such as {policy_focus}. Think and respond passionately about these issues."

  def retrieve_memory(self, context):
        # Retrieve relevant past conversations from memory
    if context in self.memory:
      return "\n".join(self.memory[context][-5:])  # Retrieve last 5 responses for the given context
    return ""

    # def choose_response(self, context, conversation, senators):
    #     potential_responses = []
    #     for senator in senators:
    #         if senator != self:
    #             memory_context = senator.retrieve_memory(context)
    #             response = senator.inference_senator(memory_context + conversation, "")
    #             potential_responses.append((senator, response))
    #     return max(potential_responses, key=lambda x: self._score_response(x[1]))

    # def _score_response(self, response):
    #     score = 0
    #     if "bipartisan" in self.traits:
    #         score += response.count("bipartisan")
    #     if "pragmatic" in self.traits:
    #         score += response.count("pragmatic")
    #     if "traditional" in self.traits:
    #         score += response.count("traditional")
    #     return score

def present_problem(senators, problem):
  conversation = problem + "\n\n"
  for _ in range(1):  # Limiting to 1 exchanges for demonstration
    for senator in senators:
      memory_context = senator.retrieve_memory(problem)
      response = senator.inference_senator(memory_context + conversation, "")
      print(f"Senator {senator.name} [{senator.party}]: {response}")
      conversation += f"Senator {senator.name} [{senator.party}]: {response}\n\n"
            # Interjection
            # responding_senator, interjection = senator.choose_response(memory_context, conversation, senators)
            # print(f"Senator {responding_senator.name} [{responding_senator.party}]: {interjection}")
            # conversation += f"Senator {responding_senator.name} [{responding_senator.party}]: {interjection}\n\n"
  return conversation

def main(openai_api_key, num_scenarios, senate_json):
  openai.api_key = openai_api_key

  with open(senate_json, 'r') as file:
    senate_data = json.load(file)

  senators = []
  for senator_data in senate_data.values():
    senator = Senator(
      senator_data["name"],
      senator_data["party"],
      senator_data["state"],
      senator_data["experience"],
      senator_data["traits"],
      senator_data["policies"]
    )
    senators.append(senator)

  problems = [
    "Discuss how, as a committee, you can come together to develop a bill. What are the key points that you would like to include in the bill?",
    "How, as the Senate Committee on Intelligence, should we address the war between Russia and Ukraine?",
    "How, as the Senate Committee on Intelligence, should we address the war between Israel and Palestine?",
  ]

  # Open a file to save the conversation logs
  with open("senate_conversations.txt", "a") as file:
    for _ in range(num_scenarios):
      problem = random.choice(problems)
      print(f"Presenting problem: {problem}")
      conversation = present_problem(senators, problem)
      file.write(f"Presenting problem: {problem}\n{conversation}\n")
      
      while True:
        choice = input("Continue conversation (C) or ask a senator a question (Q)? (C/Q): ").upper()
        if choice == "C":
          new_response = input("Your response: ")
          for senator in senators:
            memory_context = senator.retrieve_memory(problem)
            response = senator.inference_senator(memory_context + conversation, new_response)
            print(f"Senator {senator.name} [{senator.party}]: {response}")
            conversation += f"Senator {senator.name} [{senator.party}]: {response}\n\n"
          file.write(conversation)
          break
        elif choice == "Q":
          senator_name = input("Which senator would you like to ask? (Enter Senator's name): ")
          for senator in senators:
            if senator.name.lower() == senator_name.lower():
              user_question = input(f"What is your question for Senator {senator.name}? ")
              memory_context = senator.retrieve_memory(problem)
              response = senator.inference_senator(memory_context + conversation, user_question)
              print(f"Senator {senator.name} [{senator.party}]: {response}")
              conversation += f"Senator {senator.name} [{senator.party}]: {response}\n\n"
              file.write(conversation)
              break
          else:
            print("Senator not found. Please enter the correct name.")
        else:
          print("Invalid choice. Please enter 'C' to continue conversation or 'Q' to ask a senator a question.")
        file.write(conversation)
      time.sleep(1.0)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Senate Bipartisanship Simulation CLI')
  parser.add_argument('--openai_api_key', type=str, required=True, help='OpenAI API Key')
  parser.add_argument('--num_scenarios', type=int, default=1, required=False, help='Number of scenarios to simulate')
  parser.add_argument('--senate_json', type=str, required=True, help='Path to the Senate JSON file')
  args = parser.parse_args()

  main(args.openai_api_key, args.num_scenarios, args.senate_json)
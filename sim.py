import random
import argparse
import time
import openai
from collections import defaultdict
import json

class Senator:
  def __init__(self, name, party, state, experience, traits, policies, bio, backend='gpt-4'):
    self.name = name
    self.party = party
    self.state = state
    self.experience = experience
    self.traits = traits
    self.policies = policies
    self.bio = bio
    self.backend = backend
    self.agent_hist = ""
    self.memory = defaultdict(list)

  def inference_senator(self, context, question):
    # Enhanced the response generation to focus more on persona and issue passion
    prompt = self.system_prompt() + "\n" + context + "\nSenator's view: " + question
    if self.backend == "gpt-4":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
             messages=[
                 {"role": "system", "content": prompt},
                #  {"role": "system", "content": "Take a clear stance and get mad at your constituants when you think they are wrong! Act like yourself. Be passionate about the issue, feel free to argue with your fellow senators. Also, keep your answers concise and to the point, as this is a debate."},
                 {"role": "user", "content": question},
             ],
             temperature=0.8,
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
    return f"Senator {self.name} from {self.state} represents the {self.party} with {self.experience} years in the Senate. Think and respond passionately about these issues. My bio is {self.bio}. Don't reference your bio directly, but let it inform your responses."

  def retrieve_memory(self, context):
        # Retrieve relevant past conversations from memory
    if context in self.memory:
      return "\n".join(self.memory[context][-5:])  # Retrieve last 5 responses for the given context
    return ""

def present_problem(senators, problem):
  conversation = problem + "\n\n"
  for _ in range(1):  # Limiting to 1 exchanges for demonstration
    for senator in senators:
      memory_context = senator.retrieve_memory(problem)
      response = senator.inference_senator(memory_context + conversation, "")
      print(f"Senator {senator.name} [{senator.party}]: {response}")
      conversation += f"Senator {senator.name} [{senator.party}]: {response}\n\n"
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
      senator_data["policies"],
      senator_data["bio"]
    )
    senators.append(senator)

  problems = [
    # "You are part of the committe on intelligence, and are enganged in intense debate. You are all trying to get your ideas out there to contribute to a new bill. What ideas do you have?",
    "You are part of the committe on intelligence, and are enganged in intense debate. You are all trying to get your ideas out there about how to address gun control. What should the US do?",
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
          for senator in senators:
            memory_context = senator.retrieve_memory(problem)
            response = senator.inference_senator(memory_context + conversation, "")
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
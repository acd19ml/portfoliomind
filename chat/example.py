from chat import process_email
from config import example_email
from utils import pretty_print
from chat import agent
def main():
    # Process the example email
    response = process_email(example_email)
    
    # Print the response messages
    for message in response["messages"]:
        pretty_print(message)
    # response = agent.invoke(
    #     {"messages": [{
    #         "role": "user", 
    #         "content": "what is my availability for tuesday?"
    #     }]}
    # )

    response["messages"][-1].pretty_print()

if __name__ == "__main__":
    main() 
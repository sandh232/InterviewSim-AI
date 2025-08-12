# # from app.interview_graph import run_interview
# from app.server import app


# if __name__ == "__main__":
#     # print("🎯 Mock Interview Agent - Local Test Mode")
#     # print("Type 'exit' to quit, 'reset' to start over\n")
#     # session_store = {}
#     # user_id = "test_user"
#     # while True:
#     #     try:echo "gunicorn --bind=0.0.0.0 --timeout 600 main:app" > startup.sh
#     #         user_input = input("You: ").strip()
#     #         if user_input.lower() in ["exit", "quit"]:
#     #             print("👋 Good luck with your interviews!")
#     #             break
#     #         if user_input.lower() == "reset":
#     #             session_store.clear()
#     #             print("Session reset. Starting fresh!\n")
#     #             continue
#     #         response = run_interview(user_id, user_input, session_store)
#     #         print(f"Coach: {response}\n")
#     #     except KeyboardInterrupt:
#     #         print("\n👋 Goodbye!")
#     #         break
#     #     except Exception as e:
#     #         print(f"Error: {e}\n")
    
#     # Run the Flask app with debug mode enabled
#     app.run(host='0.0.0.0', port=7700, debug=True, use_reloader=True)

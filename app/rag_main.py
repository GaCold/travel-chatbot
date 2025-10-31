from location_router import LocationRouter

router = LocationRouter()

while True:
    query = input("\n🧭 Bạn hỏi gì: ")
    if query.lower() in ["exit", "quit"]:
        break
    answer = router.route_and_answer(query)
    print(f"🤖 {answer}")

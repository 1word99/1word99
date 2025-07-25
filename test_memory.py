from osmanli_ai.core.memory import ConversationMemory


def test_add_message():
    memory = ConversationMemory(max_history_length=5)
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    history = memory.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"


def test_get_history():
    memory = ConversationMemory(max_history_length=5)
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    history = memory.get_history()
    assert isinstance(history, list)
    assert len(history) == 2


def test_clear_history():
    memory = ConversationMemory(max_history_length=5)
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    memory.clear_history()
    history = memory.get_history()
    assert len(history) == 0


def test_max_history_length():
    memory = ConversationMemory(max_history_length=3)
    memory.add_message("user", "1")
    memory.add_message("assistant", "2")
    memory.add_message("user", "3")
    memory.add_message("assistant", "4")
    history = memory.get_history()
    assert len(history) == 3
    assert history[0]["content"] == "2"
    assert history[1]["content"] == "3"
    assert history[2]["content"] == "4"

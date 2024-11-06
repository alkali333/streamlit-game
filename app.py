import streamlit as st
import openai
import random
import json
from typing import Dict, Any

# Configure OpenAI client
client = openai.OpenAI()  # Make sure to set OPENAI_API_KEY in your environment


def generate_openai_response(system_prompt: str, user_prompt: str) -> str:
    """Generate response from OpenAI API"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def create_monster(hp: int) -> Dict[str, Any]:
    """Create a monster with specified HP"""
    system_prompt = """You are a game API that must return ONLY valid JSON matching this exact format:
    {"monster": {"name": "MONSTER_NAME", "description": "MONSTER_DESCRIPTION", "weapons": ["WEAPON1", "WEAPON2"], "hp": HP_VALUE}}
    
    Rules:
    1. The response must be ONLY the JSON object, no other text
    2. The "hp" value must be the number provided
    3. "weapons" must be an array of strings
    4. All values must use double quotes
    5. No trailing commas
    """

    user_prompt = (
        f"Create a unique monster with exactly HP {hp}. Return only the JSON object."
    )

    response = generate_openai_response(system_prompt, user_prompt)
    try:
        # Clean the response string of any potential whitespace or markdown formatting
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        monster_data = json.loads(response)
        # Ensure HP is set correctly
        monster_data["monster"]["hp"] = hp
        return monster_data
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw response: {response}")
        return {
            "monster": {
                "name": "Fallback Monster",
                "description": "A mysterious creature",
                "weapons": ["claws"],
                "hp": hp,
            }
        }


def generate_battle_narrative(
    narrative_type: str, hero_hp: int = None, monster_hp: int = None
) -> str:
    """Generate battle narrative based on the type of action"""
    system_prompt = f"""You are narrating a battle in a fantasy game between a hero called {st.session_state.hero['name']} and a monster called {st.session_state.monster['name']} . 
    Please use the below details to create the narrative. Make it dramatic."""

    if narrative_type == "intro":
        user_prompt = f"Introduce the battle. The setting is a futuristic city. Make it dramatic. 150 words max."
    else:
        user_prompt = get_battle_prompt(narrative_type, hero_hp, monster_hp)

    return generate_openai_response(system_prompt, user_prompt)


def get_battle_prompt(action_type: str, hero_hp: int, monster_hp: int) -> str:
    """Get the appropriate battle prompt based on the action type"""
    base_message = {
        "hero_hit": f"The user has hit the monster, the monster now has {monster_hp} health.",
        "monster_hit": f"The user has been hit by a monster and now has {hero_hp} health.",
        "hero_miss": "The user missed the monster.",
        "hero_death": "The user was killed by the monster",
        "monster_death": "The user has killed the monster",
    }

    return (
        base_message[action_type]
        + " Only describe the combat, no introduction or information about the surrounding area. 50 words only. "
    )


def initialize_game():
    """Initialize the game state"""
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.hero = {
            "name": "Cyber Knight",
            "weapons": ["Energy Sword", "Plasma Shield"],
            "hp": 30,
        }
        st.session_state.monster = None
        st.session_state.battle_log = []
        st.session_state.current_narrative = ""
        st.session_state.is_hero_turn = True
        st.session_state.loading = False


def handle_hero_turn():
    """Process hero's attack"""
    st.session_state.loading = True
    if random.random() > 0.3:  # 70% hit chance
        damage = random.randint(5, 15)
        st.session_state.monster["hp"] -= damage
        narrative = generate_battle_narrative(
            "hero_hit", None, st.session_state.monster["hp"]
        )

        if st.session_state.monster["hp"] <= 0:
            narrative = generate_battle_narrative("monster_death")
            st.session_state.game_started = False
        st.session_state.is_hero_turn = False
    else:
        narrative = generate_battle_narrative("hero_miss")
        st.session_state.is_hero_turn = False

    st.session_state.battle_log.append(narrative)
    st.session_state.current_narrative = narrative
    st.session_state.loading = False


def handle_monster_turn():
    """Process monster's attack"""
    st.session_state.loading = True
    if random.random() > 0.4:  # 60% hit chance
        damage = random.randint(3, 12)
        st.session_state.hero["hp"] -= damage
        narrative = generate_battle_narrative(
            "monster_hit", st.session_state.hero["hp"]
        )

        if st.session_state.hero["hp"] <= 0:
            narrative = generate_battle_narrative("hero_death")
            st.session_state.game_started = False
        st.session_state.is_hero_turn = True
    else:
        narrative = generate_battle_narrative("hero_miss")
        st.session_state.is_hero_turn = True

    st.session_state.battle_log.append(narrative)
    st.session_state.current_narrative = narrative
    st.session_state.loading = False


def main():
    st.title("Cyber Fantasy Battle Arena")
    initialize_game()

    # Start new battle
    if not st.session_state.game_started and st.button("Start New Battle"):
        st.session_state.loading = True
        st.session_state.game_started = True
        st.session_state.hero["hp"] = 30
        monster_hp = random.randint(5, 50)
        st.session_state.monster = create_monster(monster_hp)["monster"]
        st.session_state.is_hero_turn = True
        intro_narrative = generate_battle_narrative("intro")
        st.session_state.battle_log = [intro_narrative]
        st.session_state.current_narrative = intro_narrative
        st.session_state.loading = False
        st.rerun()

    # Show loading spinner if any operation is in progress
    if st.session_state.get("loading", False):
        st.spinner("Loading...")

    # Display game state
    if st.session_state.game_started:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Hero")
            st.write(f"Name: {st.session_state.hero['name']}")
            st.write(f"HP: {st.session_state.hero['hp']}")
            st.write("Weapons:", ", ".join(st.session_state.hero["weapons"]))

        with col2:
            st.subheader("Monster")
            st.write(f"Name: {st.session_state.monster['name']}")
            st.write(f"HP: {st.session_state.monster['hp']}")
            st.write("Weapons:", ", ".join(st.session_state.monster["weapons"]))

        # Show whose turn it is
        turn_text = (
            "Hero's Turn!" if st.session_state.is_hero_turn else "Monster's Turn!"
        )
        st.subheader(turn_text)

        # Action button
        button_text = "Attack!" if st.session_state.is_hero_turn else "Next Turn"
        if st.button(button_text):
            if st.session_state.is_hero_turn:
                handle_hero_turn()
            else:
                handle_monster_turn()
            st.rerun()

    # Display only the latest battle narrative
    st.subheader("Battle Narrative")
    if hasattr(st.session_state, "current_narrative"):
        st.markdown(f"*{st.session_state.current_narrative}*")


if __name__ == "__main__":
    main()

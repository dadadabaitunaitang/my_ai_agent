import json
import requests
import streamlit as st
from openai import OpenAI


def get_real_weather(city_name):
    try:
        url = f"https://wttr.in/{city_name}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            return f"查询失败，接口状态码：{response.status_code}"
    except Exception as e:
        return f"网络请求发生错误：{str(e)}"



tools_list = [{
    "type": "function",
    "function": {
        "name": "get_real_weather",
        "description": "查询中国指定城市当天的真实实时天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city_name": {"type": "string", "description": "城市名称，例如：北京, 上海"}
            },
            "required": ["city_name"]
        }
    }
}]




st.set_page_config(page_title="AI 天气助手", page_icon="🌤️")
st.title("🌤️ 我的全栈 AI 助手")
st.caption("我不仅有记忆，还能真正连上互联网查天气！")


client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/v1"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个全能的AI助手，回答尽量简洁。"}]


for msg in st.session_state.messages:
    if msg["role"] in ["system", "tool"] or (msg["role"] == "assistant" and msg.get("tool_calls")):
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("问我任何问题，比如：深圳今天天气怎么样？"):

    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考..."):

            response1 = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages,
                tools=tools_list
            )
            ai_message = response1.choices[0].message

            if ai_message.tool_calls:
                st.session_state.messages.append(ai_message.model_dump())

                for tool_call in ai_message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    city = args.get("city_name")

                    st.toast(f"正在通过互联网查询 {city} 的真实天气...", icon="🌍")


                    real_weather_data = get_real_weather(city)

                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": real_weather_data
                    })

                response2 = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=st.session_state.messages
                )
                final_reply = response2.choices[0].message.content
                st.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})

            else:
                st.markdown(ai_message.content)
                st.session_state.messages.append({"role": "assistant", "content": ai_message.content})
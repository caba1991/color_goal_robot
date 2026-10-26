#!/usr/bin/env python3

import json
import os
import urllib.error
import urllib.request

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


ALLOWED_COLORS = {"red", "blue", "green"}


class CommandAINode(Node):

    def __init__(self):
        super().__init__("command_ai_node")

        self.publisher = self.create_publisher(
            String,
            "/target_color",
            10
        )

        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            self.get_logger().error(
                "OPENAI_API_KEYが設定されていません"
            )

        self.get_logger().info(
            "command_ai_nodeを起動しました"
        )

    def classify_with_ai(self, user_text):
        """
        自然言語をred/blue/greenのいずれかに分類する。
        """

        if not self.api_key:
            return None

        system_prompt = """
あなたはロボット制御用の分類器です。
ユーザーの指示から目的地の色を分類してください。

出力できる文字列は次の3つだけです。
red
blue
green

必ず次のJSON形式だけで回答してください。
{"color":"red"}

説明文やMarkdownは出力しないでください。
"""

        request_body = {
            "model": "gpt-4o-mini",
            "temperature": 0,
            "response_format": {
                "type": "json_object"
            },
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        }

        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:
                response_text = response.read().decode("utf-8")

            response_json = json.loads(response_text)

            content = response_json["choices"][0]["message"]["content"]

            result = json.loads(content)
            color = result.get("color", "")

            color = color.strip().lower()

            if color not in ALLOWED_COLORS:
                self.get_logger().error(
                    f"AIの出力が不正です: {color}"
                )
                return None

            return color

        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8")
            self.get_logger().error(
                f"AI API HTTPエラー: {error.code}"
            )
            self.get_logger().error(error_body)
            return None

        except urllib.error.URLError as error:
            self.get_logger().error(
                f"AI API接続エラー: {error}"
            )
            return None

        except Exception as error:
            self.get_logger().error(
                f"AI処理中にエラーが発生しました: {error}"
            )
            return None

    def publish_color(self, color):
        """
        red/blue/greenをROSトピックへ送信する。
        """

        if color not in ALLOWED_COLORS:
            self.get_logger().error(
                f"許可されていない色です: {color}"
            )
            return

        message = String()
        message.data = color

        self.publisher.publish(message)

        self.get_logger().info(
            f"/target_colorへ送信しました: {color}"
        )

    def run_once(self):
        """
        ユーザーから1回入力を受け取り、AIで分類する。
        """

        user_text = input(
            "ロボットへの指示を入力してください "
            "（例：青へ行って）: "
        )

        if not user_text.strip():
            self.get_logger().error(
                "入力が空です"
            )
            return False

        self.get_logger().info(
            f"ユーザー入力: {user_text}"
        )

        color = self.classify_with_ai(user_text)

        if color is None:
            self.get_logger().error(
                "目的地を判定できませんでした"
            )
            return False

        self.get_logger().info(
            f"AIの判定結果: {color}"
        )

        self.publish_color(color)

        return True


def main(args=None):
    rclpy.init(args=args)

    node = CommandAINode()

    try:
        while rclpy.ok():
            node.run_once()

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

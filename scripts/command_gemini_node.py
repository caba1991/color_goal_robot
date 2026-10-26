#!/usr/bin/env python3

import json
import os
import urllib.error
import urllib.parse
import urllib.request

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


ALLOWED_COLORS = {"red", "blue", "green"}


class CommandGeminiNode(Node):

    def __init__(self):
        super().__init__("command_gemini_node")

        self.publisher = self.create_publisher(
            String,
            "/target_color",
            10
        )

        self.api_key = os.environ.get("GEMINI_API_KEY")

        self.model = os.environ.get(
            "GEMINI_MODEL",
            "gemini-2.0-flash"
        )

        if not self.api_key:
            self.get_logger().error(
                "GEMINI_API_KEYが設定されていません"
            )

        self.get_logger().info(
            f"Geminiモデル: {self.model}"
        )

    def classify_with_gemini(self, user_text):
        """
        ユーザーの自然言語をred/blue/greenに分類する。
        """

        if not self.api_key:
            return None

        prompt = f"""
あなたはロボット制御用の分類器です。

ユーザーの指示から、ロボットの目的地の色を分類してください。
目的地として選べる色は次の3つだけです。

- red
- blue
- green

回答は必ず次のJSON形式だけにしてください。

{{"color": "red"}}

red、blue、green以外の値を使わないでください。
説明文やMarkdownは不要です。

ユーザーの指示：
{user_text}
"""

        encoded_key = urllib.parse.quote(self.api_key)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={encoded_key}"
        )

        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json"
            }
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
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

            candidates = response_json.get("candidates", [])

            if not candidates:
                self.get_logger().error(
                    "Gemini APIの回答候補がありません"
                )
                return None

            parts = (
                candidates[0]
                .get("content", {})
                .get("parts", [])
            )

            if not parts:
                self.get_logger().error(
                    "Gemini APIの回答本文がありません"
                )
                return None

            content = parts[0].get("text", "").strip()

            self.get_logger().info(
                f"Gemini raw output: {content}"
            )

            result = json.loads(content)

            color = result.get("color", "")
            color = color.strip().lower()

            if color not in ALLOWED_COLORS:
                self.get_logger().error(
                    f"許可されていない色です: {color}"
                )
                return None

            return color

        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8")

            self.get_logger().error(
                f"Gemini API HTTPエラー: {error.code}"
            )
            self.get_logger().error(error_body)

            return None

        except urllib.error.URLError as error:
            self.get_logger().error(
                f"Gemini API接続エラー: {error}"
            )
            return None

        except json.JSONDecodeError as error:
            self.get_logger().error(
                f"JSONの解析に失敗しました: {error}"
            )
            return None

        except Exception as error:
            self.get_logger().error(
                f"Gemini処理中にエラーが発生しました: {error}"
            )
            return None

    def publish_color(self, color):
        """
        分類結果を/target_colorへ送信する。
        """

        if color not in ALLOWED_COLORS:
            self.get_logger().error(
                f"不正な色のため送信しません: {color}"
            )
            return

        message = String()
        message.data = color

        self.publisher.publish(message)

        self.get_logger().info(
            f"/target_colorへ送信: {color}"
        )

    def run_once(self):
        """
        ユーザーから1回入力を受け取り、Geminiで分類する。
        """

        try:
            user_text = input(
                "ロボットへの指示を入力してください "
                "（例：青へ行って）: "
            )
        except EOFError:
            return False

        if not user_text.strip():
            self.get_logger().error(
                "入力が空です"
            )
            return True

        self.get_logger().info(
            f"ユーザー入力: {user_text}"
        )

        color = self.classify_with_gemini(user_text)

        if color is None:
            self.get_logger().error(
                "目的地を判定できませんでした"
            )
            return True

        self.get_logger().info(
            f"Geminiの判定結果: {color}"
        )

        self.publish_color(color)

        return True


def main(args=None):
    rclpy.init(args=args)

    node = CommandGeminiNode()

    try:
        while rclpy.ok():
            if not node.run_once():
                break

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

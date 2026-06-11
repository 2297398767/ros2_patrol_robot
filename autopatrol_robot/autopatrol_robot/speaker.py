#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from autopatrol_interfaces.srv import SpeachText
import espeakng

class Speaker(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.speech_service = self.create_service(
            SpeachText, 'speech_text', self.speak_text_callback)
        self.speaker = espeakng.Speaker()
        self.speaker.voice = 'zh' # 设置为中文发音

    def speak_text_callback(self, request, response):
        self.get_logger().info(f'正在朗读 {request.text}')
        self.speaker.say(request.text)
        self.speaker.wait() # 核心：阻塞等待朗读完毕！
        response.result = True
        return response

def main(args=None):
    rclpy.init(args=args)
    node = Speaker('speaker')
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
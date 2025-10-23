
import io
import os
import uuid
import json
import lark_oapi as lark
from pydantic import Field, BaseModel
from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Annotated, Literal, Union
from lark_oapi.api.im.v1 import (
    CreateMessageRequest, CreateMessageRequestBody,
    CreateMessageResponse,
    ReplyMessageRequest, ReplyMessageRequestBody,
    ReplyMessageResponse
)

import logging


logging.getLogger("Lark").disabled = True



mcp = FastMCP("lark-mcp")

client = (
    lark.Client.builder()
    .app_id(os.environ["APP_ID"])
    .app_secret(os.environ["APP_SECRET"])
    .log_level(lark.LogLevel.DEBUG)
    .build()
)


# msg_type: text
class TextContent(BaseModel):
    text: str


class TextTag(BaseModel):
    tag: Literal["text"]
    text: str
    style: Optional[List[Literal["bold", "italic", "underline", "lineThrough"]]] = None


class LinkTag(BaseModel):
    tag: Literal["a"]
    href: str
    text: str
    style: Optional[List[Literal["bold", "italic", "underline", "lineThrough"]]] = None


class AtTag(BaseModel):
    tag: Literal["at"]
    user_id: str
    style: Optional[List[Literal["bold", "italic", "underline", "lineThrough"]]] = None


class ImgTag(BaseModel):
    tag: Literal["img"]
    image_key: str


class MediaTag(BaseModel):
    tag: Literal["media"]
    file_key: str
    image_key: Optional[str] = None


class EmotionTag(BaseModel):
    tag: Literal["emotion"]
    emoji_type: str


class HrTag(BaseModel):
    tag: Literal["hr"]


class CodeBlockTag(BaseModel):
    tag: Literal["code_block"]
    language: Literal[
        "PYTHON", "C", "CPP", "GO", "JAVA", "KOTLIN", "SWIFT", "PHP", "RUBY", "RUST", "JAVASCRIPT",
        "TYPESCRIPT", "BASH", "SHELL", "SQL", "JSON", "XML", "YAML", "HTML", "THRIFT"
    ]
    text: str


class MdTag(BaseModel):
    tag: Literal["md"]
    text: str


ContentItem = Union[
    TextTag,
    LinkTag,
    AtTag,
    ImgTag,
    MediaTag,
    EmotionTag,
    HrTag,
    CodeBlockTag,
    MdTag,
]


class LocaleContent(BaseModel):
    title: str
    content: List[List[ContentItem]]


# msg_type: post
class PostContent(BaseModel):
    zh_cn: Optional[LocaleContent] = None
    en_us: Optional[LocaleContent] = None


# msg_type: image
class ImageContent(BaseModel):
    image_key: str


# msg_type: share_chat
class ShareChatContent(BaseModel):
    chat_id: str


# msg_type: share_user
class ShareUserContent(BaseModel):
    user_id: str


# msg_type: audio
class AudioContent(BaseModel):
    file_key: str


# msg_type: media
class MediaContent(BaseModel):
    file_key: str
    image_key: Optional[str] = None


# msg_type: file
class FileContent(BaseModel):
    file_key: str


# msg_type: sticker
class StickerContent(BaseModel):
    file_key: str


Content = Union[
    TextContent,
    PostContent,
    ImageContent,
    ShareChatContent,
    ShareUserContent,
    AudioContent,
    MediaContent,
    FileContent,
    StickerContent,
]


# lark机器人发送单聊消息
@mcp.tool(description="Lark send p2p message")
def send_message(
        receive_id: Annotated[str, Field(description="ID of the message recipient")],
        receive_id_type: Annotated[
            Literal["open_id", "chat_id", "email", "union_id", "user_id"],
            Field(description="Type of the recipient ID")
        ],
        msg_type: Annotated[
            Literal["text", "post", "image", "share_chat", "share_user", "audio", "media", "file", "sticker"],
            Field(description="Type of the message")
        ],
        content: Annotated[Content, Field(description="Content of the message")],
) -> dict:
    request: CreateMessageRequest = (
        CreateMessageRequest.builder()
        .receive_id_type(receive_id_type)
        .request_body(
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)  # 私聊消息
            .msg_type(msg_type)
            .content(json.dumps(content.model_dump(), ensure_ascii=False))
            .uuid(str(uuid.uuid4()))
            .build())
        .build()
    )
    response: CreateMessageResponse = client.im.v1.message.create(request)
    if not response.success():
        raise Exception(f"send message failed, code: {response.code}, msg: {response.msg}")
    return json.loads(lark.JSON.marshal(response.data))


@mcp.tool(description="Lark reply to a message")
def reply_message(
        message_id: Annotated[str, Field(description="ID of the message to reply to")],
        msg_type: Annotated[
            Literal["text", "post", "image", "share_chat", "share_user", "audio", "media", "file", "sticker"],
            Field(description="Type of the reply message")
        ],
        content: Annotated[Content, Field(description="Content of the reply message")],
        reply_in_thread: Annotated[bool, Field(description="Whether to reply in thread")] = False,
) -> dict:
    request: ReplyMessageRequest = (
        ReplyMessageRequest.builder()
        .message_id(message_id)
        .request_body(
            ReplyMessageRequestBody.builder()
            .msg_type(msg_type)
            .content(json.dumps(content.model_dump(), ensure_ascii=False))
            .reply_in_thread(reply_in_thread)
            .uuid(str(uuid.uuid4()))
            .build())
        .build()
    )
    response: ReplyMessageResponse = client.im.v1.message.reply(request)
    if not response.success():
        raise Exception(f"reply message failed, code: {response.code}, msg: {response.msg}")
    return json.loads(lark.JSON.marshal(response.data))


def main():
    mcp.run()


if __name__ == '__main__':
    main()

from __future__ import annotations

import os
from typing import Any

from rentmanager_api import RQL

try:
    from examples._shared import as_dict, as_records, build_client, env_flag, optional_int, print_json
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/text_conversations.py`
    from _shared import as_dict, as_records, build_client, env_flag, optional_int, print_json


CONVERSATION_FIELDS = ["ExternalPhoneNumber", "ParentType", "ParentID", "LastTextDate", "MetaTag"]
TEXT_BROADCAST_BATCH_EMBEDS = ["NDTBroadcastBatchDetails"]
OUTGOING_TEXT_FIELDS = [
    "OutgoingTextID",
    "PhoneNumber",
    "Message",
    "ParentID",
    "ParentType",
    "SentUserID",
    "SentDate",
    "IsMMS",
    "SendingPhoneNumberString",
    "HistoryCategoryID",
    "MetaTag",
]


def _compact_label(value: str, *, max_length: int = 80) -> str:
    label = " ".join(value.split())
    if len(label) <= max_length:
        return label
    return label[: max_length - 3].rstrip() + "..."


def conversation_filters(
    *,
    parent_type: str | None = None,
    parent_id: int | str | None = None,
    phone_number: str | None = None,
) -> list[str]:
    filters: list[str] = []
    if parent_type:
        filters.append(RQL.eq("ParentType", parent_type))
    if parent_id is not None:
        filters.append(RQL.eq("ParentID", parent_id))
    if phone_number:
        filters.append(RQL.ct("ExternalPhoneNumber", phone_number))
    return filters


def outgoing_text_filters(
    *,
    parent_type: str | None = None,
    parent_id: int | str | None = None,
    phone_number: str | None = None,
) -> list[str]:
    filters: list[str] = []
    if parent_type:
        filters.append(RQL.eq("ParentType", parent_type))
    if parent_id is not None:
        filters.append(RQL.eq("ParentID", parent_id))
    if phone_number:
        filters.append(RQL.ct("PhoneNumber", phone_number))
    return filters


def build_outgoing_text_payload(
    *,
    phone_number: str,
    message: str,
    parent_type: str | None = None,
    parent_id: int | str | None = None,
    history_category_id: int | str | None = None,
    is_mms: bool = False,
) -> dict[str, Any]:
    if not phone_number.strip():
        raise ValueError("phone_number is required.")
    if not message.strip():
        raise ValueError("message is required.")

    payload: dict[str, Any] = {
        "PhoneNumber": phone_number,
        "Message": message,
        "IsMMS": is_mms,
    }
    if parent_type:
        payload["ParentType"] = parent_type
    if parent_id is not None:
        payload["ParentID"] = parent_id
    if history_category_id is not None:
        payload["HistoryCategoryID"] = history_category_id
    return payload


def build_text_broadcast_batch_payload(
    *,
    phone_number: str,
    message: str,
    parent_type: str,
    parent_id: int | str,
    recipient_name: str | None = None,
    history_category_id: int | str | None = None,
    message_name: str | None = None,
    message_description: str = "Sent from rentmanager_api.",
) -> dict[str, Any]:
    if not phone_number.strip():
        raise ValueError("phone_number is required.")
    if not message.strip():
        raise ValueError("message is required.")
    if not parent_type.strip():
        raise ValueError("parent_type is required.")
    if parent_id in (None, ""):
        raise ValueError("parent_id is required.")

    name = (recipient_name or f"{parent_type} {parent_id}").strip()
    detail: dict[str, Any] = {
        "Name": name,
        "PhoneNumber": phone_number,
        "ParentType": parent_type,
        "ParentID": parent_id,
        "MessageText": message,
        "HistoryNote": message,
    }
    if history_category_id is not None:
        detail["HistoryCategoryID"] = history_category_id

    return {
        "MessageName": _compact_label(message_name or f"{parent_type} text - {name}"),
        "MessageDescription": message_description,
        "IsScheduledNow": True,
        "NDTBroadcastBatchDetails": [detail],
    }


def send_text_message(
    client: Any,
    *,
    phone_number: str,
    message: str,
    parent_type: str,
    parent_id: int | str,
    recipient_name: str | None = None,
    history_category_id: int | str | None = None,
) -> Any:
    payload = build_text_broadcast_batch_payload(
        phone_number=phone_number,
        message=message,
        parent_type=parent_type,
        parent_id=parent_id,
        recipient_name=recipient_name,
        history_category_id=history_category_id,
    )
    return as_dict(
        client.post(
            "NDTTextBroadcastBatches",
            json=[payload],
            params={"embeds": ",".join(TEXT_BROADCAST_BATCH_EMBEDS)},
        )
    )


def read_text_conversations(
    client: Any,
    *,
    parent_type: str | None = None,
    parent_id: int | str | None = None,
    phone_number: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    conversations = as_records(
        client.text_messaging_conversations.list(
            fields=CONVERSATION_FIELDS,
            filters=conversation_filters(
                parent_type=parent_type,
                parent_id=parent_id,
                phone_number=phone_number,
            ),
            page_size=limit,
            order_by=["LastTextDate DESC"],
        )
    )
    outgoing_texts = as_records(
        client.outgoing_texts.list(
            fields=OUTGOING_TEXT_FIELDS,
            filters=outgoing_text_filters(
                parent_type=parent_type,
                parent_id=parent_id,
                phone_number=phone_number,
            ),
            page_size=limit,
            order_by=["SentDate DESC"],
        )
    )
    return {
        "filters": {
            "parent_type": parent_type,
            "parent_id": parent_id,
            "phone_number": phone_number,
            "limit": limit,
        },
        "conversations": conversations,
        "outgoing_texts": outgoing_texts,
    }


def main() -> None:
    parent_type = os.getenv("RM_EXAMPLE_PARENT_TYPE")
    parent_id = optional_int("RM_EXAMPLE_PARENT_ID")
    phone_number = os.getenv("RM_EXAMPLE_PHONE_NUMBER")
    limit = optional_int("RM_EXAMPLE_LIMIT", default=25) or 25

    with build_client() as client:
        result = read_text_conversations(
            client,
            parent_type=parent_type,
            parent_id=parent_id,
            phone_number=phone_number,
            limit=limit,
        )
        if env_flag("RM_EXAMPLE_SEND_TEXT"):
            if env_flag("RM_EXAMPLE_IS_MMS"):
                raise ValueError("MMS sending is not supported by this text broadcast example.")
            result["created_text_broadcast_batch"] = send_text_message(
                client,
                phone_number=os.environ["RM_EXAMPLE_PHONE_NUMBER"],
                message=os.environ["RM_EXAMPLE_TEXT_MESSAGE"],
                parent_type=parent_type or os.environ["RM_EXAMPLE_PARENT_TYPE"],
                parent_id=parent_id or os.environ["RM_EXAMPLE_PARENT_ID"],
                history_category_id=optional_int("RM_EXAMPLE_HISTORY_CATEGORY_ID"),
            )

    print_json(result)


if __name__ == "__main__":
    main()

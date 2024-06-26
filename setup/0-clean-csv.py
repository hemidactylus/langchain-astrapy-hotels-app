import os
from typing import cast

import numpy as np
import pandas as pd

from setup.setup_constants import (
    HOTEL_REVIEW_FILE_NAME,
    MAX_REVIEW_TEXT_LENGTH,
    MAX_REVIEW_TITLE_LENGTH,
    RAW_REVIEW_SOURCE_FILE_NAME,
)
from utils.reviews import generate_review_id

# Script that cleans up the raw CSV data and stores it in a new CSV:
#  - Picks only the columns of interest.
#  - Cleans up trailing truncation marker from truncated reviews.
#  - Assigns a synthetic, unique review_id because the original dataset does not contain one.
#
# The resulting CSV file will be used as the review data in subsequent setup steps.


this_dir = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    hotel_review_file_path = os.path.join(this_dir, HOTEL_REVIEW_FILE_NAME)
    if os.path.isfile(hotel_review_file_path):
        print(
            f"File '{HOTEL_REVIEW_FILE_NAME}' exists already. Running this "
            "step again results in new random review IDs and you'll have to "
            "recompute the embeddings.\nIf you really want to, please delete "
            f"file '{HOTEL_REVIEW_FILE_NAME}' manually."
        )
    else:
        raw_review_source_file_path = os.path.join(
            this_dir, RAW_REVIEW_SOURCE_FILE_NAME
        )
        raw_csv = pd.read_csv(raw_review_source_file_path)
        chosen_columns = pd.DataFrame(
            raw_csv,
            columns=[
                "id",
                "reviews.date",
                "city",
                "country",
                "latitude",
                "longitude",
                "name",
                "reviews.rating",
                "reviews.text",
                "reviews.title",
                "reviews.username",
            ],
        )

        rename_map = {
            "id": "hotel_id",
            "reviews.date": "date",
            "city": "hotel_city",
            "country": "hotel_country",
            "latitude": "hotel_latitude",
            "longitude": "hotel_longitude",
            "name": "hotel_name",
            "reviews.rating": "rating",
            "reviews.text": "text",
            "reviews.title": "title",
            "reviews.username": "username",
        }
        renamed_csv = chosen_columns.rename(columns=rename_map)

        DISCARDABLE_ENDING_WITH_SPACE = "... More"
        DISCARDABLE_ENDING_WITHOUT_SPACE = "...More"

        def clean_review_text(row: pd.Series) -> str:
            text0 = cast(str, row["text"])
            #
            if text0.find(DISCARDABLE_ENDING_WITH_SPACE) > -1:
                text1 = text0[: text0.find(DISCARDABLE_ENDING_WITH_SPACE)]
            else:
                text1 = text0
            #
            if text1.find(DISCARDABLE_ENDING_WITHOUT_SPACE) > -1:
                text2 = text1[: text1.find(DISCARDABLE_ENDING_WITHOUT_SPACE)]
            else:
                text2 = text1
            # sanitize for extremely long texts
            return text2[:MAX_REVIEW_TEXT_LENGTH]

        def clean_review_title(row: pd.Series) -> str:
            title0 = cast(str, row["title"])
            return title0[:MAX_REVIEW_TITLE_LENGTH]

        def review_id(row: pd.Series) -> str:
            return generate_review_id()

        renamed_csv["title"] = renamed_csv["title"].fillna("(No title)")
        renamed_csv["text"] = renamed_csv["text"].fillna("(No review text)")
        renamed_csv["id"] = renamed_csv.apply(review_id, axis=1)
        renamed_csv["text"] = renamed_csv.apply(clean_review_text, axis=1)
        renamed_csv["title"] = renamed_csv.apply(clean_review_title, axis=1)
        renamed_csv["review_upvotes"] = np.random.randint(1, 21, size=len(renamed_csv))

        file_name = hotel_review_file_path
        renamed_csv.to_csv(file_name)

        print(f"[0-clean-csv.py] Cleaned CSV saved to {file_name}")

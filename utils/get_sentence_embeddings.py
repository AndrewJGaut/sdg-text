from copy import deepcopy
import gensim.downloader as gensim_api
from nltk.stem import WordNetLemmatizer
import numpy as np
import pandas as pd
import os
from sentence_transformers import SentenceTransformer
import string
import re
from keywords import CHARMELEON_KEYWORDS_DICT
import random
import mwparserfromhell


def _extract_relevant_sentences_by_row(text, keywords, lemmatize_model=None):
    """
    Extracts sentences from text that contain any of the keywords.

    Args:
        `keywords`: List of lemmatized keywords
        `text`: Text to return sentences from

    Returns:
        List of sentences that contain at least one of the keywords.
    """
    if not text:
        return None

    parsed_wikicode = mwparserfromhell.parse(text)
    text = parsed_wikicode.strip_code()

    sentences = text.split(".")
    relevant_sentences = []

    for sentence in sentences:
        words = sentence.split(" ")
        if any(
            [
                lemmatize_model.lemmatize(word) if lemmatize_model else word in keywords
                for word in words
            ]
        ):
            relevant_sentences.append(sentence)

    return relevant_sentences if relevant_sentences else None


def _embed_sentences_by_row(x, sentence_embed_model):
    return np.mean(sentence_embed_model.encode(x), axis=0) if x else None


def write_metadata_and_embeddings(metadata, embeddings, output_data_dir):
    metadata_output_data_path = os.path.join(output_data_dir, "metadata.csv")
    embeddings_output_data_path = os.path.join(output_data_dir, "embeddings.npy")

    if not os.path.isdir(output_data_dir):
        os.makedirs(output_data_dir)

    with open(metadata_output_data_path, "a") as f:
        metadata.to_csv(f, header=f.tell() == 0, index=False)

    if os.path.exists(embeddings_output_data_path):
        embeddings_old = np.load(embeddings_output_data_path)
        embeddings = np.concatenate([embeddings_old, embeddings])
    print(f"Embeddings shape: {embeddings.shape}")
    np.save(
        embeddings_output_data_path, embeddings,
    )


def embed_sentences(
    input_data_path,
    output_data_dir,
    sentence_embed_model,
    keywords_dict,
    lemmatize_model=None,
):
    """
    Given metadata and articles stored in `input_data_path`,
    writes metadata and averaged sentence embeddings to `output_data_dir`.

    Args:
        `input_data_path`: Input data path
        `output_data_dir`: Output data dir
        `lemmatize_model`: Model for lemmatizing words
        `sentence_embed_model`: Model for generating sentence embeddings
        `keywords_dict`: Model for keywords for each target

    Returns:
        None
    """
    df = pd.read_json(input_data_path)
    df["DHSID_EA"] = df["tag"].apply(lambda x: x[:-5])
    df["cname"] = df["DHSID_EA"].apply(lambda x: x[:2])
    df = df[df["cname"] != "no"]
    df = df[["DHSID_EA", "cname", "clean_text"]]

    print(f"Evaluating {df.shape[0]} examples")

    for target, keywords in keywords_dict.items():
        print(f"Creating embeddings for target {target}")

        df[f"clean_text_{target}"] = df["clean_text"].apply(
            lambda x: _extract_relevant_sentences_by_row(x, keywords, lemmatize_model)
        )
        df_for_target = df[~df[f"clean_text_{target}"].isna()]

        print(f"Found relevant sentences for {df_for_target.shape[0]} examples")

        embeddings = np.zeros((df_for_target.shape[0], 384))
        for i, text in enumerate(df_for_target[f"clean_text_{target}"]):
            embeddings[i, :] = _embed_sentences_by_row(text, sentence_embed_model)

        print(
            f"Writing embeddings for target {target} and countries {df_for_target.cname.unique()}"
        )

        df_for_target = df_for_target.reset_index(drop=True)
        for country in df_for_target.cname.unique():
            country_idx = df_for_target[df_for_target.cname == country].index.values
            write_metadata_and_embeddings(
                metadata=df_for_target.loc[country_idx, "DHSID_EA"],
                embeddings=embeddings[country_idx, :],
                output_data_dir=os.path.join(output_data_dir, country, target),
            )


if __name__ == "__main__":
    input_data_dir = "data/wikipedia"
    output_data_dir = "data/intermediate_embeddings"

    lemmatize_model = WordNetLemmatizer()

    # good mixture of small size and high sentence embedding performance from sentence-transformers
    # learn more here: https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2
    sentence_embed_model = SentenceTransformer("all-MiniLM-L12-v2")

    files_embedded = []
    for file in os.listdir(input_data_dir):
        print(f"Starting to embed {file}")
        embed_sentences(
            input_data_path=os.path.join(input_data_dir, file),
            output_data_dir=output_data_dir,
            sentence_embed_model=sentence_embed_model,
            keywords_dict=CHARMELEON_KEYWORDS_DICT,
            # lemmatize_model=lemmatize_model,
        )
        files_embedded.append(file)
        print(f"Have embedded {files_embedded}\n")

import modal
from numpy import ndarray

stub = modal.Stub("text-embeddings")


dockerfile_image = modal.Image.from_dockerfile("Dockerfile-modal")
sentence_transformer = None


def _get_sentence_transformer():
    from sentence_transformers.SentenceTransformer import SentenceTransformer

    global sentence_transformer

    if sentence_transformer is None:
        DEFAULT_SENTENCE_MODEL = "cambridgeltl/tweet-roberta-base-embeddings-v1"

        sentence_transformer = SentenceTransformer(DEFAULT_SENTENCE_MODEL)
        sentence_transformer.to("cpu")
        sentence_transformer.eval()

    return sentence_transformer


@stub.function(image=dockerfile_image)
def get_text_embeddings(text) -> ndarray:
    import torch

    sentence_transformer = _get_sentence_transformer()

    single_input_flag = type(text) is str
    texts = [text] if single_input_flag else text
    assert all(type(t) is str for t in texts), "All items must be strings"
    batch_size = len(texts)

    with torch.no_grad():
        vectors = sentence_transformer.encode(
            texts, batch_size=batch_size, show_progress_bar=False
        )[0]

    return vectors

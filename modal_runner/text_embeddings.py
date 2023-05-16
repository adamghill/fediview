from modal import Image, Stub, method
from modal.cls import ClsMixin
from numpy import ndarray

stub = Stub("text-embeddings")

dockerfile_image = Image.from_dockerfile("Dockerfile-modal")


@stub.cls(image=dockerfile_image)
class Roberta(ClsMixin):
    def __enter__(self):
        self.sentence_transformer = self._get_sentence_transformer()

    def _get_sentence_transformer(self):
        from sentence_transformers.SentenceTransformer import SentenceTransformer

        DEFAULT_SENTENCE_MODEL = "cambridgeltl/tweet-roberta-base-embeddings-v1"

        sentence_transformer = SentenceTransformer(DEFAULT_SENTENCE_MODEL)
        sentence_transformer.to("cpu")
        sentence_transformer.eval()

        return sentence_transformer

    @method()
    def get_text_embeddings(self, text) -> ndarray:
        import torch

        single_input_flag = type(text) is str
        texts = [text] if single_input_flag else text
        assert all(type(t) is str for t in texts), "All items must be strings"
        batch_size = len(texts)

        with torch.no_grad():
            vectors = self.sentence_transformer.encode(
                texts, batch_size=batch_size, show_progress_bar=False
            )[0]

        return vectors

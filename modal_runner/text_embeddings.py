import logging

from modal import Image, SharedVolume, Stub, method
from modal.cls import ClsMixin
from numpy import mean, ndarray

logger = logging.getLogger(__name__)

volume = SharedVolume()
stub = Stub("text-embeddings")


dockerfile_image = Image.from_dockerfile("Dockerfile-modal")


@stub.cls(image=dockerfile_image, shared_volumes={"/root/roberta": volume})
class Roberta(ClsMixin):
    cache_folder = "/root/roberta"

    def __enter__(self):
        from sentence_transformers.SentenceTransformer import SentenceTransformer

        self.sentence_transformer = SentenceTransformer(
            "cambridgeltl/tweet-roberta-base-embeddings-v1",
            cache_folder=self.cache_folder,
        )
        self.sentence_transformer.to("cpu")
        self.sentence_transformer.eval()

    @method()
    def get_text_embeddings(self, text) -> ndarray:
        import torch

        single_input_flag = type(text) is str
        texts = [text] if single_input_flag else text
        assert all(type(t) is str for t in texts), "All items must be strings"
        batch_size = 20

        with torch.no_grad():
            logger.info("Create vectors")

            vectors = self.sentence_transformer.encode(
                texts, batch_size=batch_size, show_progress_bar=False
            )

            if single_input_flag:
                vectors = vectors[0]
            else:
                vectors = mean(vectors, axis=0)

        return vectors

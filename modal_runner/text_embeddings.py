import logging

from modal import App, Image, NetworkFileSystem, enter, method
from numpy import mean, ndarray

logger = logging.getLogger(__name__)

nfs = NetworkFileSystem.from_name("my-nfs", create_if_missing=True)
app = App("text-embeddings")


dockerfile_image = Image.from_dockerfile("Dockerfile-modal")


@app.cls(image=dockerfile_image, network_file_systems={"/root/roberta": nfs})
class Roberta:
    cache_folder = "/root/roberta"

    @enter()
    def enter(self):
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

        single_input_flag = isinstance(text, str)
        texts = [text] if single_input_flag else text
        assert all(isinstance(t, str) for t in texts), "All items must be strings"
        batch_size = 20

        with torch.no_grad():
            logger.info("Create vectors")

            vectors = self.sentence_transformer.encode(texts, batch_size=batch_size, show_progress_bar=False)

            if single_input_flag:
                vectors = vectors[0]
            else:
                vectors = mean(vectors, axis=0)

        return vectors

from modal import Image, SharedVolume, Stub, method
from modal.cls import ClsMixin
from numpy import ndarray

volume = SharedVolume()
stub = Stub("text-embeddings")


dockerfile_image = Image.from_dockerfile("Dockerfile-modal")


@stub.cls(image=dockerfile_image, shared_volumes={"/root/roberta": volume})
class Roberta(ClsMixin):
    def __enter__(self):
        from sentence_transformers.SentenceTransformer import SentenceTransformer

        self.sentence_transformer = SentenceTransformer(
            "cambridgeltl/tweet-roberta-base-embeddings-v1",
            cache_folder="/root/roberta",
        )
        self.sentence_transformer.to("cpu")
        self.sentence_transformer.eval()

    @method()
    def get_text_embeddings(self, text) -> ndarray:
        import torch

        single_input_flag = type(text) is str
        texts = [text] if single_input_flag else text
        assert all(type(t) is str for t in texts), "All items must be strings"
        batch_size = len(texts)

        with torch.no_grad():
            print("Create vectors")
            vectors = self.sentence_transformer.encode(
                texts, batch_size=batch_size, show_progress_bar=False
            )[0]

        return vectors

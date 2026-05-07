from src.search.indexer import InvertedIndex
from src.ml.classifier import DocumentClassifier

idx = InvertedIndex()
idx.load_index()

clf = DocumentClassifier()
# Treinar com os 110 documentos
accuracy = clf.prepare_and_train(idx.documents)

# Testar uma predição manual
nova_area = clf.predict_category(
    "Deep Learning for Vision", 
    "This research focuses on neural networks and computer vision."
)
print(f"\ns Predição para novo doc: {nova_area}")
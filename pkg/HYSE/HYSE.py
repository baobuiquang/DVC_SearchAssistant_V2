# HYSE - HYbrid SEarch: Lexical-based search (BM25) + Semantic Search (SentenceTransformers)

# ====================================================================================================

from huggingface_hub import hf_hub_download as HF_Download
import onnxruntime as ort
import numpy as np
import os
from pkg.NLPT.NLPT import Process_NLPT_Normalize
from pkg.NLPT.NLPT import Process_NLPT_Tokenize

from rank_bm25 import BM25Okapi as BM25_Retriever
from tokenizers import Tokenizer as STL_Tokenizer

# ====================================================================================================

class SentenceTransformerLite:
    # Init: model_path -> model + tokenizer
    def __init__(self, model_path):
        try:
            # Model (ONNX)
            try: HF_Download(repo_id=model_path, filename="onnx/model.onnx_data")
            except: pass
            STL_model = ort.InferenceSession(HF_Download(repo_id=model_path, filename="onnx/model.onnx"))
            # Tokenizer
            STL_tokenizer = STL_Tokenizer.from_pretrained(model_path)
            STL_tokenizer.enable_padding(pad_id=1, pad_token="<pad>")
            STL_tokenizer.enable_truncation(max_length=512)
        except:
            raise ValueError("⚠️ > SentenceTransformerLite > init")
        # Return
        self.STL_model = STL_model
        self.STL_tokenizer = STL_tokenizer
    # Encode: Text(s) -> Embedding(s)
    def encode(self, inputtexts):
        # Ensure inputtexts is a list of strings
        if isinstance(inputtexts, list) and all(isinstance(e, str) for e in inputtexts):
            if len(inputtexts) == 0:
                raise ValueError("⚠️ > SentenceTransformerLite > encode > Empty list []")
        elif isinstance(inputtexts, str):
            inputtexts = [inputtexts]
        else:
            raise ValueError("⚠️ > SentenceTransformerLite > encode")
        # Tokenize
        inputs = self.STL_tokenizer.encode_batch(inputtexts, is_pretokenized=False)
        inputs_ids = np.array([e.ids for e in inputs], dtype=np.int64)
        inputs_msk = np.array([e.attention_mask for e in inputs], dtype=np.int64)
        # Encoding
        embeddings = self.STL_model.run(None, {"input_ids": inputs_ids, "attention_mask": inputs_msk})[0]                                             # Encode
        embeddings = np.sum(embeddings * np.expand_dims(inputs_msk, axis=-1), axis=1) / np.maximum(np.sum(inputs_msk, axis=1, keepdims=True), 1e-9)   # Pooling
        embeddings = embeddings / np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-9)                                                 # Normalize
        # Return
        return embeddings

class ExactMatchSearch:
    def __init__(self, save_path="ExactMatchSearch.npz"):
        self.save_path = save_path
        if not os.path.exists(save_path):
            self.docs = ["✨"]
            self.update(self.docs)
        else:
            self.load()
            self.update(self.docs)
    def update(self, new_docs):
        self.docs += list(set(new_docs) - set(self.docs))
        self.save()
    def search(self, queries):
        best_matching_docs = []
        for q in queries:
            # Exact match (with diacritics)
            tmp_docs = [d for d in self.docs if q.lower().strip() in d.lower().strip()]
            if len(tmp_docs) == 0:
                # Exact match (without diacritics)
                tmp_docs = [d for d in self.docs if Process_NLPT_Normalize(q) in Process_NLPT_Normalize(d)]
            best_matching_docs.append(tmp_docs)
        return best_matching_docs
    def save(self):
        np.savez_compressed(file=self.save_path, docs=self.docs)
    def load(self):
        saveddata = np.load(file=self.save_path, allow_pickle=True)
        self.docs = [str(e) for e in saveddata["docs"]]

class LexicalSearch:
    def __init__(self, save_path="LexicalSearch.npz"):
        self.save_path = save_path
        if not os.path.exists(save_path):
            self.docs = ["✨"]
            self.update(self.docs)
        else:
            self.load()
            self.update(self.docs)
    def update(self, new_docs):
        self.docs += list(set(new_docs) - set(self.docs))
        self.embs = [Process_NLPT_Tokenize(e) for e in self.docs]
        self.model = BM25_Retriever(self.embs)
        self.save()
    def search(self, queries, top=5):
        queries_embs = [Process_NLPT_Tokenize(e) for e in queries]
        best_matching_idxs = [self.model.get_top_n(query_emb, range(len(self.docs)), n=top) for query_emb in queries_embs]
        best_matching_docs = [[self.docs[idx] for idx in e] for e in best_matching_idxs]
        return best_matching_docs
    def save(self):
        np.savez_compressed(file=self.save_path, docs=self.docs)
    def load(self):
        saveddata = np.load(file=self.save_path, allow_pickle=True)
        self.docs = [str(e) for e in saveddata["docs"]]

class SemanticSearch:
    def __init__(self, model_path="onelevelstudio/ML-E5-0.3B", save_path="SemanticSearch.npz", compress_docs_to_keywords=False):
        self.compress_docs_to_keywords = compress_docs_to_keywords
        self.model = SentenceTransformerLite(model_path)
        self.save_path = save_path
        if not os.path.exists(save_path):
            self.docs = [str(model_path.split("/")[-1]), "✨", "\n", " ", ""]
            self.embs = self.model.encode(self.docs)
            self.save()
        else:
            self.load()
    def update(self, new_docs):
        new_docs = list(set(new_docs) - set(self.docs))
        if len(new_docs) > 0:
            self.docs += new_docs # compress_docs_to_keywords or not, still keep the original docs here, only affect the embs
            if self.compress_docs_to_keywords:
                new_docs = [", ".join(Process_NLPT_Tokenize(e)) for e in new_docs]
            new_docs_embs = self.model.encode(new_docs)
            self.embs = np.concatenate((self.embs, new_docs_embs))
            # print(f"SemanticSearch > Update > + {len(new_docs)} document(s) {'⚠️' if len(self.docs) != len(self.embs) else ''}")
            self.save()
    def save(self):
        np.savez_compressed(file=self.save_path, docs=self.docs, embs=self.embs)
        # print(f"SemanticSearch > Save > {len(self.docs)} document(s) {'⚠️' if len(self.docs) != len(self.embs) else ''}")
    def load(self):
        saveddata = np.load(file=self.save_path, allow_pickle=True)
        self.docs = [str(e) for e in saveddata["docs"]]
        self.embs = saveddata["embs"]
        # print(f"SemanticSearch > Load > {len(self.docs)} document(s) {'⚠️' if len(self.docs) != len(self.embs) else ''}")
    def search(self, queries, top=5):
        queries_embs = self.model.encode(queries)
        similarities = queries_embs @ self.embs.T
        best_matching_idxs = [[idx for idx, _ in sorted(enumerate(sim), key=lambda x: x[1], reverse=True)][:min(top, len(self.docs))] for sim in similarities]
        best_matching_docs = [[self.docs[idx] for idx in e] for e in best_matching_idxs]
        return best_matching_docs

class Object_HYSE:
    def __init__(self):
        self.search_engine_1 = ExactMatchSearch(save_path="url/hyse_db_1.npz")
        self.search_engine_2 = LexicalSearch(save_path="url/hyse_db_2.npz")
        self.search_engine_3 = SemanticSearch(model_path="onelevelstudio/ML-E5-0.3B", save_path="url/hyse_db_3.npz")
        self.search_engine_4 = SemanticSearch(model_path="onelevelstudio/MPNET-0.3B", save_path="url/hyse_db_4.npz")
    def update(self, docs):
        self.search_engine_1.update(docs)
        self.search_engine_2.update(docs)
        self.search_engine_3.update(docs)
        self.search_engine_4.update(docs)
    def search(self, queries, top=5):
        res_search_1 = self.search_engine_1.search(queries)
        res_search_2 = self.search_engine_2.search(queries)
        res_search_3 = self.search_engine_3.search(queries)
        res_search_4 = self.search_engine_4.search(queries)
        self.search_result_debug = [{"query": queries[i], "res_search_1": res_search_1[i], "res_search_2": res_search_2[i], "res_search_3": res_search_3[i], "res_search_4": res_search_4[i]} for i in range(len(res_search_1))]
        final_res = []
        for i in range(len(res_search_1)):
            res_search = res_search_1[i] + res_search_2[i] + res_search_3[i] + res_search_4[i]
            ranking = [{"score": e[1], "content": e[0]} for e in sorted({item: res_search.count(item) for item in set(res_search)}.items(), key=lambda x: (-x[1], len(x[0])))]
            final_res.append(ranking[:min(top, len(ranking))])
        return final_res
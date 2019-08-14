import os
import torch
from torch.utils.data import Dataset, DataLoader
from pytorch_transformers import BertTokenizer
from tqdm.auto import tqdm
import multiprocessing
multiprocessing.set_start_method('spawn', True)


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, input_mask, segment_ids, label_id):
        self.input_ids = torch.Tensor(input_ids)
        self.input_mask = torch.Tensor(input_mask)
        self.segment_ids = torch.Tensor(segment_ids)
        self.label_id = torch.Tensor(label_id)


class MsMarcoDataset(Dataset):
    """MsMarco preprocessing Dataset"""

    def __init__(self, tsv_file, data_dir, max_seq_len=512, size=None, transform=None):
        """
        Args:
            tsv_file (string): TSV file with triples, generated by TREC_run_to_BERT.py, formatted like
                "qid-did    query   document    label"
            data_dir (string): Directory with the rest of the data, where we can write to
            size (int, optional): Number of lines to process. If None, will run wc -l first.
            transform (callable, optional): Transformations to be performed on the data
        """
        self.tsv_path = tsv_file
        self.data_dir = data_dir
        self.transform = transform
        self.max_seq_len = max_seq_len
        if size is None:
            with open(tsv_file) as f:
                for i, _ in enumerate(f):
                    pass
            self.size = i + 1
        else:
            self.size = size

        self.offset_dict, self.index_dict = self.load_offset_dict()
        assert os.path.isdir(os.path.join(self.data_dir, "models"))
        self.tokenizer = BertTokenizer.from_pretrained(
            os.path.join(self.data_dir, "models"))
        self.label_map = {label: i for i, label in enumerate(["0", "1"])}

    def load_offset_dict(self):
        offset_dict = {}
        index_dict = {}
        with open(self.tsv_path, encoding="utf-8") as f:
            pbar = tqdm(total=self.size, desc="Computing offset dictionary")
            location = f.tell()
            line = f.readline()
            pbar.update()
            idx = 0
            while line:
                [did, query, document, label] = line.split("\t")
                offset_dict[did] = location
                index_dict[idx] = did
                location = f.tell()
                line = f.readline()
                pbar.update()
                idx += 1

        return offset_dict, index_dict

    def __getitem__(self, did):
        if isinstance(did, str):
            offset = self.offset_dict[did]
        elif isinstance(did, int):
            offset = self.offset_dict[self.index_dict[did]]
        else:
            raise NotImplementedError(
                "can only fetch integer or string indexes")
        with open(self.tsv_path) as f:
            f.seek(offset)
            line = f.readline()
        return self.text_to_features(line)

    def __len__(self):
        return self.size

    def _truncate_seq_pair(self, tokens_a, tokens_b, max_length):
        """Truncates a sequence pair in place to the maximum length."""
        while True:
            total_length = len(tokens_a) + len(tokens_b)
            if total_length <= max_length:
                break
            if len(tokens_a) > len(tokens_b):
                tokens_a.pop()
            else:
                tokens_b.pop()

    def text_to_features(self, sample):

        line = sample.strip().split("\t")
        text_a = line[1]
        text_b = line[2]
        label = line[-1]

        tokens_a = self.tokenizer.tokenize(text_a)
        tokens_b = self.tokenizer.tokenize(text_b)

        self._truncate_seq_pair(tokens_a, tokens_b, self.max_seq_len - 3)
        tokens = ["[CLS]"] + tokens_a + ["[SEP]"] + tokens_b + ["[SEP]"]

        segment_ids = [0] * (len(tokens_a) + 2)
        segment_ids += [1] * (len(tokens_b) + 1)

        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        input_mask = [1] * len(input_ids)
        padding = [0] * (self.max_seq_len - len(input_ids))
        input_ids += padding
        input_mask += padding
        segment_ids += padding

        assert len(input_ids) == self.max_seq_len, "input_id"
        assert len(input_mask) == self.max_seq_len, "input_mask"
        assert len(segment_ids) == self.max_seq_len, "segment_ids"

        label_id = self.label_map[label]
        return torch.Tensor(input_ids), torch.Tensor(input_mask), torch.Tensor(segment_ids), torch.Tensor([label_id])

if __name__ == "__main__":
    dataset = MsMarcoDataset(
        "/ssd2/arthur/TREC2019/data/small_sample.tsv", "/ssd2/arthur/TREC2019/data")
    data_loader = DataLoader(
        dataset, batch_size=32, shuffle=True)
    for  (input_ids, input_masks, segment_ids, label_ids) in tqdm(data_loader):
        pass
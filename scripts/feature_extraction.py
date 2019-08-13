from __future__ import absolute_import, division, print_function
import argparse
import logging
import os
import random
import numpy as np
import torch
from pytorch_transformers import BertTokenizer
from run_classifier_dataset_utils import load_dataset

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_name", default="msmarco", type=str,
                        help="Task name")
    parser.add_argument("--do_lower_case", action="store_true",
                        help="should use bert uncased?")
    parser.add_argument("--data_dir", required=True, type=str,
                        help="Directory with MSmarco data")
    parser.add_argument("--bert_model", default="bert-base-uncased",
                        help="BERT model to be used")
    parser.add_argument("--max_seq_length", default=512,
                        type=int, help="Number of tokens to cap BERT at")
    parser.add_argument("--batch_size", default=128, type=int,
                        help="Number of batches to process data")
    parser.add_argument("--eval", action="store_true",
                        help="Use eval dataset?")
    parser.add_argument("--force_reload", action="store_true",
                        help="Force reload dataset")
    parser.add_argument("--expected_len", required=True, type=int,
                        help="Expected number of samples to be loaded")
    parser.add_argument("--reverse_label", action="store_true",
                        help="""Bert for Sequence prediction expects 0 when the
                         next squence is True. Should we revert to 1?""")

    args = parser.parse_args()
    output_dir = os.path.join(args.data_dir, "models")

    tokenizer = BertTokenizer.from_pretrained(output_dir,
                                              do_lower_case=args.do_lower_case)
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)

    # loading dataset
    load_dataset(args.task_name, args.bert_model, args.max_seq_length,
                 args.data_dir, tokenizer, args.batch_size, eval=args.eval,
                 return_examples=False, force_reload=args.force_reload,
                 expected_len=args.expected_len, load_only=True)


if __name__ == "__main__":
    main()

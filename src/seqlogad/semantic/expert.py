"""Standalone trained semantic adapter, independent of future sequence/fusion experts."""
from pathlib import Path
from .config import load_config, identity
from .contracts import read
from .checkpoint import verify_checkpoint
from .model import load_model
from .scoring import score_message
from seqlogad.common.checksum import sha256_file


class SemanticExpert:
    @classmethod
    def from_checkpoint(cls, repo_root, run_directory, checkpoint_name=None):
        run = Path(run_directory)
        cfg = read(run / 'config.yaml')
        defaults, base = load_config(repo_root)
        for key in ['model_id', 'model_revision', 'tokenizer_id', 'tokenizer_revision', 'base_config_sha256', 'expert_id']:
            if cfg[key] != defaults[key]:
                raise ValueError('expert incompatible with frozen base')
        manifest = read(run / 'manifest.json')
        checkpoint = run / 'checkpoints' / (checkpoint_name or manifest['best_checkpoint'])
        if not checkpoint.resolve().is_relative_to((run / 'checkpoints').resolve()):
            raise ValueError('checkpoint path outside run')
        expected = dict(manifest['identity'], config_sha256=identity(cfg))
        verify_checkpoint(checkpoint, expected)
        model, tokenizer, dtype = load_model(cfg, base, checkpoint / 'adapter')
        if str(dtype) != manifest['precision']:
            raise ValueError('inference precision differs from trained run')
        model.eval()
        instance = cls()
        instance.model, instance.tokenizer, instance.cfg = model, tokenizer, cfg
        instance.metadata = {'fold_id': manifest['fold_id'],
            'checkpoint_sha256': sha256_file(checkpoint / 'adapter/adapter_model.safetensors'),
            'input_manifest_sha256': manifest['data_manifest_sha256'], 'context_config_sha256': identity(cfg)}
        return instance

    def score(self, normalized_message, architecture_id, record_id):
        return score_message(self.model, self.tokenizer, self.cfg, normalized_message,
            dict(self.metadata, architecture_id=architecture_id, unit_id=record_id, record_ids=[record_id]))

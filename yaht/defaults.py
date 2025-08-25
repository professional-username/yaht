DEFAULT_CONFIG_FILE = "yaht.yaml"
DEFAULT_CACHE_DIR = ".yaht_cache"

DEFAULT_CONFIG = """
SETTINGS:
  cache_dir: .yaht_cache

default_experiment:
  results: M, X

  structure:
    n1 <- return_n: _ -> N
    return_inverse: N -> M
    n2 <- return_n: _ -> X

  trials:
    trial1:
      n1.n: 5
    trial2:
      n1.n: 3
      n2.n: 30

  parameters:
    n2.n: -50
"""

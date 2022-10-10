TIME_ZONE = 'Asia/Shanghai'
NUM_LHS_SAMPLES = 10
MIN_WORKLOAD_RESULTS_COUNT = 5
KNOB_IDENT_USE_PRUNED_METRICS = False
ENABLE_DUMMY_ENCODER = False
DEFAULT_CONVERSION = '''{
        "BYTES_SYSTEM": {
            "PiB": "1024 ** 5",
            "TiB": "1024 ** 4",
            "GiB": "1024 ** 3",
            "MiB": "1024 ** 2",
            "KiB": "1024 ** 1"
        },
        "MIN_BYTES_UNIT": "KB",
        "TIME_SYSTEM": {
            "d": "1000 * 60 * 60 * 24",
            "h": "1000 * 60 * 60",
            "m": "1000 * 60",
            "s": "1000",
            "ms": "1"
        },
        "MIN_TIME_UNIT": "ms"
    }'''
DEFAULT_HYPER_PARAMETERS = '''{
        "DDPG_ACTOR_HIDDEN_SIZES": [128, 128, 64],
        "DDPG_ACTOR_LEARNING_RATE": 0.02,
        "DDPG_CRITIC_HIDDEN_SIZES": [64, 128, 64],
        "DDPG_CRITIC_LEARNING_RATE": 0.001,
        "DDPG_BATCH_SIZE": 32,
        "DDPG_GAMMA": 0.0,
        "DDPG_SIMPLE_REWARD": true,
        "DDPG_UPDATE_EPOCHS": 30,
        "DDPG_USE_DEFAULT": false,
        "DNN_DEBUG": true,
        "DNN_DEBUG_INTERVAL": 100,
        "DNN_EXPLORE": false,
        "DNN_EXPLORE_ITER": 500,
        "DNN_GD_ITER": 100,
        "DNN_NOISE_SCALE_BEGIN": 0.1,
        "DNN_NOISE_SCALE_END": 0.0,
        "DNN_TRAIN_ITER": 100,
        "FLIP_PROB_DECAY": 0.5,
        "GPR_BATCH_SIZE": 3000,
        "GPR_DEBUG": true,
        "GPR_EPS": 0.001,
        "GPR_EPSILON": 1e-06,
        "GPR_LEARNING_RATE": 0.01,
        "GPR_LENGTH_SCALE": 2.0,
        "GPR_MAGNITUDE": 1.0,
        "GPR_MAX_ITER": 500,
        "GPR_MAX_TRAIN_SIZE": 7000,
        "GPR_MU_MULTIPLIER": 1.0,
        "GPR_MODEL_NAME": "BasicGP",
        "GPR_HP_LEARNING_RATE": 0.001,
        "GPR_HP_MAX_ITER": 5000,
        "GPR_RIDGE": 1.0,
        "GPR_SIGMA_MULTIPLIER": 1.0,
        "GPR_UCB_SCALE": 0.2,
        "GPR_USE_GPFLOW": true,
        "GPR_UCB_BETA": "get_beta_td",
        "IMPORTANT_KNOB_NUMBER": 10000,
        "INIT_FLIP_PROB": 0.3,
        "NUM_SAMPLES": 30,
        "TF_NUM_THREADS": 4,
        "TOP_NUM_CONFIG": 10}'''

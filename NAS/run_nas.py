from utils.get_torch_data_loader import *
from utils.get_data_loader import *
import nni.retiarii.evaluator.pytorch.lightning as pl
from nni.retiarii import serialize
import nni.retiarii.strategy as strategy
from nni.retiarii.experiment.pytorch import RetiariiExeConfig, RetiariiExperiment, debug_mutated_model
from utils.constants import DATA_DIR
import random
import pdb


def run_nas(model_class, target,features, model_batch_size=32, model_epochs=10,  model_type="classification"):
    """

    :param model: should be the class inheriting from nni.retiarii.nn.pytorch.Module which has some
    Mutation Primitives (see here: https://nni.readthedocs.io/en/stable/NAS/MutationPrimitives.html)
    :return:
    """
    """
    #ds =
    raw_train_dataset = SustainBenchTextTorchDataset(
        data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="train"
    )
    raw_test_dataset =SustainBenchTextTorchDataset(
        data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="test"
    )

    ds = SustainBenchTextDataset(features=features, target=target, model_type=model_type, classification_threshold=0, data_dir=DATA_DIR)
    train_x, train_y = ds.get_data("train")
    test_x, test_y = ds.get_data("test")


    model = model_class(input_dim=len(raw_train_dataset), model_type = model_type)

    #pdb.set_trace()
    """
    """
    train_dataset = serialize(raw_train_dataset, data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="train", train=True, download=True)
    test_dataset = serialize(raw_test_dataset, data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="test", train=False, download=True)
    #train_dataset = raw_train_dataset
    #test_dataset = raw_test_dataset
    #train_dataset = serialize(raw_test_dataset)
    #test_dataset = serialize(test_dataset)
    train_dataset=serialize(train_x, train_y)
    test_dataset = serialize(test_x,test_y)
    trainer = pl.Classification(train_dataloader=pl.DataLoader(train_dataset, batch_size=model_batch_size),
                                val_dataloaders=pl.DataLoader(test_dataset, batch_size=model_batch_size),
                                max_epochs=model_epochs)
    """
    #raw_train_dataset = SustainBenchTextTorchTrainDatasetForNAS()
    #model = model_class(input_dim=len(raw_train_dataset), model_type=model_type)
    #train_dataset = serialize()
    #test_dataset = serialize(SustainBenchTextTorchTestDatasetForNAS())
    raw_train_dataset = SustainBenchTextTorchDataset(
        data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="train"
    )
    raw_test_dataset = SustainBenchTextTorchDataset(
        data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="test"
    )
    #model = model_class(input_dim=len(raw_train_dataset), model_type=model_type)
    model = model_class(input_dim=384, model_type=model_type)
    train_dataset = serialize(SustainBenchTextTorchDataset, data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="train")
    test_dataset = serialize(SustainBenchTextTorchDataset, data_dir=DATA_DIR,
        features=features,
        target=target,
        model_type=model_type,
        data_split="test")
    trainer = pl.Classification(train_dataloader=pl.DataLoader(train_dataset, batch_size=model_batch_size),
                                val_dataloaders=pl.DataLoader(test_dataset, batch_size=model_batch_size),
                                max_epochs=model_epochs)
    simple_strategy = strategy.Random()

    exp = RetiariiExperiment(model, trainer, [], simple_strategy)

    exp_config = RetiariiExeConfig('local')
    exp_config.experiment_name = 'NAS_search_random_strategy'
    exp_config.trial_concurrency = 2
    exp_config.max_trial_number = 20
    exp_config.training_service.use_active_gpu = False
    exp_config.execution_engine="base"
    export_formatter = 'dict'

    # uncomment this for graph-based execution engine
    # exp_config.execution_engine = 'base'
    # export_formatter = 'code'

    exp.run(exp_config, 8081 + random.randint(0, 100))
    print('Final model:')
    for model_code in exp.export_top_models(formatter=export_formatter):
        print(model_code)

import os
from .dataloader import *
from config import EvalSetting
from utils import ModelType


def data_preparation(config, model, dataset, save=False):
    es = EvalSetting(config)

    # es.group_by_user()
    es.shuffle()
    es.split_by_ratio(config['split_ratio'])

    builded_datasets = dataset.build(es)
    train_dataset, valid_dataset, test_dataset = builded_datasets
    names = ['train', 'valid', 'test']
    sampler = Sampler(config, names, builded_datasets)

    if save:
        save_datasets(config['checkpoint_dir'], name=names, dataset=builded_datasets)

    es.neg_sample_by(1, real_time=True)
    train_data = dataloader_construct(
        name='train',
        config=config,
        eval_setting=es,
        dataset=train_dataset,
        sampler=sampler,
        phase='train',
        dl_type=model.type,
        dl_format=config['input_format'],
        batch_size=config['train_batch_size'],
        shuffle=True
    )

    es.neg_sample_to(config['test_neg_sample_num'])
    valid_data, test_data = dataloader_construct(
        name='evaluation',
        config=config,
        eval_setting=es,
        dataset=[valid_dataset, test_dataset],
        sampler=sampler,
        phase=['valid', 'test'],
        dl_type=model.type,
        batch_size=config['eval_batch_size']
    )

    return train_data, valid_data, test_data


def dataloader_construct(name, config, eval_setting, dataset, sampler, phase,
                         dl_type=ModelType.GENERAL, dl_format='pointwise',
                         batch_size=1, shuffle=False):
    if not isinstance(dataset, list):
        dataset = [dataset]
    if not isinstance(phase, list):
        phase = [phase]

    if not isinstance(batch_size, list):
        batch_size = [batch_size] * len(dataset)

    if len(dataset) != len(batch_size):
        raise ValueError('dataset {} and batch_size {} should have the same length'.format(dataset, batch_size))
    if len(dataset) != len(phase):
        raise ValueError('dataset {} and phase {} should have the same length'.format(dataset, phase))

    print('Build [{}] DataLoader for [{}] with format [{}]\n'.format(dl_type, name, dl_format))
    print(eval_setting)
    print('batch_size = {}, shuffle = {}\n'.format(batch_size, shuffle))

    if dl_type == ModelType.GENERAL:
        DataLoader = get_data_loader(eval_setting.neg_sample_args)
    else:
        raise NotImplementedError('dl_type [{}] has not been implemented'.format(dl_type))

    ret = []

    for i, (ds, ph) in enumerate(zip(dataset, phase)):
        dl = DataLoader(
            config=config,
            dataset=ds,
            sampler=sampler,
            phase=ph,
            neg_sample_args=eval_setting.neg_sample_args,
            batch_size=batch_size[i],
            dl_format=dl_format,
            shuffle=shuffle
        )
        ret.append(dl)

    if len(ret) == 1:
        return ret[0]
    else:
        return ret


def save_datasets(save_path, name, dataset):
    if (not isinstance(name, list)) and (not isinstance(dataset, list)):
        name = [name]
        dataset = [dataset]
    if len(name) != len(dataset):
        raise ValueError('len of name {} should equal to len of dataset'.format(name, dataset))
    for i, d in enumerate(dataset):
        cur_path = os.path.join(save_path, name[i])
        if not os.path.isdir(cur_path):
            os.makedirs(cur_path)
        d.save(cur_path)

import os
import numpy as np
from tqdm import tqdm
from skimage import io
from skimage import transform
from paths import root_dir, mkdir_if_not_exist
import pandas as pd
from PIL import Image

ISIC2018_dir = os.path.join(root_dir, 'datasets', 'ISIC2018')
data_dir = os.path.join(ISIC2018_dir, 'data')
cached_data_dir = os.path.join(ISIC2018_dir, 'cache')

mkdir_if_not_exist(dir_list=[cached_data_dir])

task12_img = 'ISIC2018_Task1-2_Training_Input'
task3_img = 'ISIC2018_Task3_Training_Input'
task1_gt = 'ISIC2018_Task1_Training_GroundTruth'
task2_gt = 'ISIC2018_Task2_Training_GroundTruth_v3'
task3_gt = 'ISIC2018_Task3_Training_GroundTruth'

MEL = 0  # Melanoma
NV = 1  # Melanocytic nevus
BCC = 2  # Basal cell carcinoma
AKIEC = 3  # Actinic keratosis / Bowen's disease (intraepithelial carcinoma)
BKL = 4  # Benign keratosis (solar lentigo / seborrheic keratosis / lichen planus-like keratosis)
DF = 5  # Dermatofibroma
VASC = 6  # Vascular lesion

classes = [MEL, NV, BCC, AKIEC, BKL, DF, VASC]
class_names = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']

task12_img_dir = os.path.join(data_dir, task12_img)
task3_img_dir = os.path.join(data_dir, task3_img)
task1_gt_dir = os.path.join(data_dir, task1_gt)
task2_gt_dir = os.path.join(data_dir, task2_gt)
task3_gt_dir = os.path.join(data_dir, task3_gt)

task12_image_ids = list()
if os.path.isdir(task12_img_dir):
    task12_image_ids = [fname.rsplit('.', maxsplit=1)[0] for fname in os.listdir(task12_img_dir)
                        if fname.startswith('ISIC') and fname.lower().endswith('.jpg')]
    task12_image_ids.sort()

task3_image_ids = list()
if os.path.isdir(task3_img_dir):
    task3_image_ids = [fname.rsplit('.', maxsplit=1)[0] for fname in os.listdir(task3_img_dir)
                       if fname.startswith('ISIC') and fname.lower().endswith('.jpg')]

    task3_image_ids.sort()

task3_gt_fname = 'ISIC2018_Task3_Training_GroundTruth.csv'
task3_sup_fname = 'ISIC2018_Task3_Training_LesionGroupings.csv'

task12_images_npy_prefix = 'task12_images'
task3_images_npy_prefix = 'task3_images'
task1_gt_npy_prefix = 'task1_masks'
task2_gt_npy_prefix = 'task2_masks'
task3_gt_npy_prefix = 'task3_labels'

task2_labels = ['globules',
                'milia_like_cyst',
                'negative_network',
                'pigment_network',
                'streaks']

ATTRIBUTE_GLOBULES = 1
ATTRIBUTE_MILIA_LIKE_CYST = 2
ATTRIBUTE_NEGATIVE_NETWORK = 3
ATTRIBUTE_PIGMENT_NETWORK = 4
ATTRIBUTE_STREAKS = 5

ATTRIBUTES = {
    'GLOBULES': 1,
    'MILIA_LIKE_CYST': 2,
    'NEGATIVE_NETWORK': 3,
    'PIGMENT_NETWORK': 4,
    'STREAKS': 5,
}


def load_image_by_id(image_id, fname_fn, from_dir, output_size=None, save_resized=False, to_dir=None):
    img_fnames = fname_fn(image_id)
    if isinstance(img_fnames, str):
        img_fnames = [img_fnames, ]

    assert isinstance(img_fnames, tuple) or isinstance(img_fnames, list)

    images = []
    for img_fname in img_fnames:
        img_path_in = os.path.join(from_dir, img_fname)
        if not os.path.exists(img_path_in):
            raise FileNotFoundError('img %s not found' % img_fname)
        image = io.imread(img_path_in)

        if output_size:
            image = transform.resize(image, (output_size, output_size),
                                     order=1, mode='constant',
                                     cval=0, clip=True,
                                     preserve_range=True,
                                     anti_aliasing=True)

        image = image.astype(np.uint8)

        if output_size and save_resized:
            img_path_out = os.path.join(to_dir, img_fname)
            im = Image.fromarray(image)
            im.save(img_path_out)

        images.append(image)

    if len(images) == 1:
        return images[0]
    else:
        return np.concatenate(images, axis=-1)  # masks


def load_images(image_ids, from_dir, output_size=None, fname_fn=None, verbose=True):
    images = []

    if verbose:
        print('loading images from', from_dir)

    for image_id in tqdm(image_ids):
        image = load_image_by_id(image_id,
                                 from_dir=from_dir,
                                 output_size=output_size,
                                 fname_fn=fname_fn)
        images.append(image)

    return images


def load_task12_training_images(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    images_npy_filename = os.path.join(cached_data_dir, '%s%s.npy' % (task12_images_npy_prefix, suffix))

    if os.path.exists(images_npy_filename):
        images = np.load(images_npy_filename)
    else:
        images = load_images(image_ids=task12_image_ids,
                             from_dir=task12_img_dir,
                             output_size=output_size,
                             fname_fn=lambda x: '%s.jpg' % x)
        images = np.stack(images).astype(np.uint8)
        np.save(images_npy_filename, images)
    return images


def load_task3_training_images(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    images_npy_filename = os.path.join(cached_data_dir, '%s%s.npy' % (task3_images_npy_prefix, suffix))

    if os.path.exists(images_npy_filename):
        images = np.load(images_npy_filename)
    else:
        images = load_images(image_ids=task3_image_ids,
                             from_dir=task3_img_dir,
                             output_size=output_size,
                             fname_fn=lambda x: '%s.jpg' % x)
        images = np.stack(images).astype(np.uint8)
        np.save(images_npy_filename, images)
    return images


def load_task1_training_masks(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    npy_filename = os.path.join(cached_data_dir, 'task1_masks%s.npy' % suffix)
    if os.path.exists(npy_filename):
        masks = np.load(npy_filename)
    else:
        masks = load_images(image_ids=task12_image_ids,
                            from_dir=task1_gt_dir,
                            output_size=output_size,
                            fname_fn=lambda x: '%s_segmentation.png' % x)
        masks = np.stack(masks)
        np.save(npy_filename, masks)
    return masks


def load_task2_training_masks(output_size=None):
    suffix = '' if output_size is None else '_%d' % output_size
    npy_filename = os.path.join(cached_data_dir, 'task2_masks%s.npy' % suffix)

    if os.path.exists(npy_filename):
        masks = np.load(npy_filename)
    else:
        masks = load_images(image_ids=task12_image_ids,
                            from_dir=task2_gt_dir,
                            output_size=output_size,
                            fname_fn=lambda x: ('%s_attribute_globules.png' % x,
                                                '%s_attribute_milia_like_cyst.png' % x,
                                                '%s_attribute_negative_network.png' % x,
                                                '%s_attribute_pigment_network.png' % x,
                                                '%s_attribute_streaks.png' % x)
                            )
        masks = np.stack(masks, axis=0)
        np.save(npy_filename, masks)

    bg_masks = masks.max() - masks.max(axis=-1)
    bg_masks = bg_masks[..., None]
    masks = np.concatenate([bg_masks, masks], axis=-1)
    return masks


def load_task3_training_labels():
    npy_filename = os.path.join(cached_data_dir, '%s.npy' % task3_gt_npy_prefix)
    if os.path.exists(npy_filename):
        labels = np.load(npy_filename)
    else:
        # image, MEL, NV, BCC, AKIEC, BKL, DF, VASC
        labels = []
        with open(os.path.join(task3_gt_dir, task3_gt_fname), 'r') as f:
            for i, line in tqdm(enumerate(f.readlines()[1:])):
                fields = line.strip().split(',')
                labels.append([eval(field) for field in fields[1:]])
        labels = np.stack(labels, axis=0)
        np.save(npy_filename, labels)
    return labels


def partition_task3_data(x, y, k=5, i=0, test_split=1. / 6, seed=42):
    assert isinstance(k, int) and isinstance(i, int) and 0 <= i < k

    fname = os.path.join(task3_gt_dir, task3_sup_fname)
    assert os.path.exists(fname)

    df = pd.read_csv(os.path.join(task3_gt_dir, task3_sup_fname))
    grouped = df.groupby('lesion_id', sort=True)
    lesion_ids = []
    for name, group in grouped:
        image_ids = group.image.tolist()
        lesion_ids.append([name, image_ids])

    # shuffle lesion ids
    np.random.seed(seed)
    n = len(lesion_ids)
    indices = np.random.permutation(n)

    image_ids = [image_id for idx in indices for image_id in lesion_ids[idx][1]]
    n = len(image_ids)
    n_set = int(n * (1. - test_split)) // k
    # divide the data into (k + 1) sets, -1 is test set, [0, k) are for train and validation
    indices = [i for i in range(k) for _ in range(n_set)] + [-1] * (n - n_set * k)

    indices = list(zip(indices, image_ids))
    indices.sort(key=lambda x: x[1])
    indices = np.array([idx for idx, image_id in indices], dtype=np.uint)

    valid_indices = (indices == i)
    test_indices = (indices == -1)
    train_indices = ~(valid_indices | test_indices)

    x_valid = x[valid_indices]
    y_valid = y[valid_indices]

    x_train = x[train_indices]
    y_train = y[train_indices]

    x_test = x[test_indices]
    y_test = y[test_indices]

    return (x_train, y_train), (x_valid, y_valid), (x_test, y_test)


def load_training_data(task_idx,
                       output_size=None,
                       num_partitions=5,
                       idx_partition=0,
                       test_split=0.):
    assert isinstance(task_idx, int) and 0 < task_idx <= 3
    if task_idx == 1:
        x = load_task12_training_images(output_size=output_size)
        y = load_task1_training_masks(output_size=output_size)
        return partition_data(x=x, y=y, k=num_partitions, i=idx_partition, test_split=test_split)

    elif task_idx == 2:
        x = load_task12_training_images(output_size=output_size)
        y = load_task2_training_masks(output_size=output_size)
        return partition_data(x=x, y=y, k=num_partitions, i=idx_partition, test_split=test_split)

    else:
        x = load_task3_training_images(output_size=output_size)
        y = load_task3_training_labels()
        return partition_task3_data(x=x, y=y, k=num_partitions, i=idx_partition, test_split=test_split)


def partition_indices(n, k=5, i=0, test_split=1. / 6, seed=42):
    n_set = int(n * (1. - test_split)) // k
    # divide the data into (k + 1) sets, -1 is test set, [0, k) are for train and validation
    indices = np.array([i for i in range(k) for _ in range(n_set)] +
                       [-1] * (n - n_set * k),
                       dtype=np.int8)

    np.random.seed(seed)
    np.random.shuffle(indices)

    valid_indices = (indices == i)
    test_indices = (indices == -1)
    train_indices = ~(valid_indices | test_indices)

    return train_indices, valid_indices, test_indices


def partition_data(x, y, k=5, i=0, test_split=1. / 6, seed=42):
    assert isinstance(k, int) and isinstance(i, int) and 0 <= i < k

    train_indices, valid_indices, test_indices = partition_indices(n=x.shape[0], k=k, i=i,
                                                                   test_split=test_split, seed=seed)

    x_valid = x[valid_indices]
    y_valid = y[valid_indices]

    x_train = x[train_indices]
    y_train = y[train_indices]

    x_test = x[test_indices]
    y_test = y[test_indices]

    return (x_train, y_train), (x_valid, y_valid), (x_test, y_test)


def get_task12_resize_img_dir(output_size=None):

    task12_img_dir_resized = task12_img_dir.replace('datasets/ISIC2018/data', 'datasets/ISIC2018/cache') \
                             + '_resize_' + str(output_size)

    task1_gt_dir_resized = task1_gt_dir.replace('datasets/ISIC2018/data', 'datasets/ISIC2018/cache') \
                           + '_resize_' + str(output_size)

    task2_gt_dir_resized = task2_gt_dir.replace('datasets/ISIC2018/data', 'datasets/ISIC2018/cache') \
                           + '_resize_' + str(output_size)

    return task12_img_dir_resized, task1_gt_dir_resized, task2_gt_dir_resized


def resize_and_save_task12(output_size=None):

    task12_img_dir_resized, task1_gt_dir_resized, task2_gt_dir_resized = get_task12_resize_img_dir(
        output_size=output_size)

    mkdir_if_not_exist([task12_img_dir_resized, task1_gt_dir_resized, task2_gt_dir_resized])

    image_id_list = task12_image_ids.copy()

    for image_id in tqdm(image_id_list):

        _ = load_image_by_id(image_id,
                             from_dir=task12_img_dir,
                             output_size=output_size,
                             fname_fn=lambda x: '%s.jpg' % x,
                             save_resized=True,
                             to_dir=task12_img_dir_resized)

        _ = load_image_by_id(image_id,
                             from_dir=task1_gt_dir,
                             output_size=output_size,
                             fname_fn=lambda x: '%s_segmentation.png' % x,
                             save_resized=True,
                             to_dir=task1_gt_dir_resized)

        _ = load_image_by_id(image_id,
                             from_dir=task2_gt_dir,
                             output_size=output_size,
                             fname_fn=lambda x: ('%s_attribute_globules.png' % x,
                                                 '%s_attribute_milia_like_cyst.png' % x,
                                                 '%s_attribute_negative_network.png' % x,
                                                 '%s_attribute_pigment_network.png' % x,
                                                 '%s_attribute_streaks.png' % x),
                             save_resized=True,
                             to_dir=task2_gt_dir_resized)


if __name__ == "__main__":
    resize_and_save_task12(output_size=1024)

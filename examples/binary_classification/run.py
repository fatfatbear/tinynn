"""Example code for binary classification."""

import argparse
import os
import time

import numpy as np
import tinynn as tn


def main(args):
    if args.seed >= 0:
        tn.seeder.random_seed(args.seed)

    train_set, _, test_set = tn.dataset.mnist(args.data_dir, one_hot=True)
    train_x, train_y = train_set
    test_x, test_y = test_set
    # convert to binary label (odd_num: 1, even_num: 0)
    train_y = (np.argmax(train_y, axis=1) % 2).reshape((-1, 1))
    test_y = (np.argmax(test_y, axis=1) % 2).reshape((-1, 1))

    if args.model_type == "mlp":
        # A multilayer perceptron model
        net = tn.net.Net([
            tn.layer.Dense(200),
            tn.layer.ReLU(),
            tn.layer.Dense(100),
            tn.layer.ReLU(),
            tn.layer.Dense(70),
            tn.layer.ReLU(),
            tn.layer.Dense(30),
            tn.layer.ReLU(),
            tn.layer.Dense(1)
        ])
    elif args.model_type == "cnn":
        # A LeNet-5 model with activation function changed to ReLU
        train_x = train_x.reshape((-1, 28, 28, 1))
        test_x = test_x.reshape((-1, 28, 28, 1))
        net = tn.net.Net([
            tn.layer.Conv2D(kernel=[5, 5, 1, 6], stride=[1, 1]),
            tn.layer.ReLU(),
            tn.layer.MaxPool2D(pool_size=[2, 2], stride=[2, 2]),
            tn.layer.Conv2D(kernel=[5, 5, 6, 16], stride=[1, 1]),
            tn.layer.ReLU(),
            tn.layer.MaxPool2D(pool_size=[2, 2], stride=[2, 2]),
            tn.layer.Flatten(),
            tn.layer.Dense(120),
            tn.layer.ReLU(),
            tn.layer.Dense(84),
            tn.layer.ReLU(),
            tn.layer.Dense(1)
        ])
    elif args.model_type == "rnn":
        # A simple recurrent neural net to classify images.
        train_x = train_x.reshape((-1, 28, 28))
        test_x = test_x.reshape((-1, 28, 28))
        net = tn.net.Net([
            tn.layer.RNN(num_hidden=50, activation=tn.layer.Tanh()),
            tn.layer.Dense(1)
        ])
    else:
        raise ValueError("Invalid argument: model_type")

    loss = tn.loss.SigmoidCrossEntropy()
    optimizer = tn.optimizer.Adam(lr=args.lr)
    model = tn.model.Model(net=net, loss=loss, optimizer=optimizer)

    if args.model_path is not None:
        model.load(args.model_path)
        evaluate(model, test_x, test_y)
    else:
        iterator = tn.data_iterator.BatchIterator(batch_size=args.batch_size)
        for epoch in range(args.num_ep):
            t_start = time.time()
            for batch in iterator(train_x, train_y):
                pred = model.forward(batch.inputs)
                loss, grads = model.backward(pred, batch.targets)
                model.apply_grads(grads)
            print("Epoch %d time cost: %.4f" % (epoch, time.time() - t_start))
            # evaluate
            evaluate(model, test_x, test_y)

        # save model
        print(model.net.layers[0].params["b"].mean())
        if not os.path.isdir(args.model_dir):
            os.makedirs(args.model_dir)
        model_name = "mnist-%s-epoch%d.pkl" % (args.model_type, args.num_ep)
        model_path = os.path.join(args.model_dir, model_name)
        model.save(model_path)
        print("model saved in %s" % model_path)


def evaluate(model, test_x, test_y):
    model.set_phase("TEST")
    test_pred_score = tn.math.sigmoid2(model.forward(test_x))
    test_pred = (test_pred_score >= 0.5).astype(int)
    print(tn.metric.precision(test_pred, test_y))
    print(tn.metric.auc(test_pred_score, test_y))
    model.set_phase("TRAIN")


if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str,
                        default=os.path.join(curr_dir, "data"))
    parser.add_argument("--model_dir", type=str,
                        default=os.path.join(curr_dir, "models"))
    parser.add_argument("--model_path", type=str, default=None)
    parser.add_argument("--model_type", default="mlp", type=str,
                        help="[*mlp|cnn|rnn]")
    parser.add_argument("--num_ep", default=10, type=int)
    parser.add_argument("--lr", default=1e-3, type=float)
    parser.add_argument("--batch_size", default=128, type=int)
    parser.add_argument("--seed", default=-1, type=int)
    args = parser.parse_args()
    main(args)


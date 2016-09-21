
import tensorflow as tf
import numpy as np
from wavenet_ops import time_to_batch, batch_to_time, causal_conv
from wavenet import WaveNet
import json


# Create a time-series of audio amplitudes corresponding to 3 superimposed
# sine waves.
def MakeSineWaves():
    sample_rate = 1.0/16000.0
    # Period of the sine wave is inverse of frequency in hz.
    p1 = 1.0/155.56  # E-flat
    p2 = 1.0/196.00  # G
    p3 = 1.0/233.08  # B-flat
    # 100 mSec of data.
    times = np.arange(0.0, 0.10, sample_rate)

    # Amplitudes
    amplitudes = (
        np.sin(times*2.0*np.pi/p1)/3.0 +
        np.sin(times*2.0*np.pi/p2)/3.0 +
        np.sin(times*2.0*np.pi/p3)/3.0
    )

    return amplitudes


class TestNet(tf.test.TestCase):
    def setUp(self):
        quantization_steps = 256
        self.net = WaveNet(batch_size=1,
                           channels=quantization_steps,
                           dilations=[1,2, 4, 8, 16, 32, 64, 128, 256,
                                      1, 2, 4, 8, 16, 32, 64, 128, 256],
                           filter_width=2,
                           residual_channels=16,
                           dilation_channels=16)

    # Train a net on a short clip of 3 sine waves superimposed
    # (an e-flat chord).
    #
    # Presumably it can overfit to such a simple signal. This test serves
    # as a smoke test where we just check that it runs end-to-end during
    # training, and learns this waveform.

    def testEndToEndTraining(self):
        audio = MakeSineWaves()
        np.random.seed(42)

        audio_tensor = tf.convert_to_tensor(audio, dtype=tf.float32)
        loss = self.net.loss(audio_tensor)
        optimizer = tf.train.AdamOptimizer(learning_rate=0.02)
        trainable = tf.trainable_variables()
        optim = optimizer.minimize(loss, var_list=trainable)
        init = tf.initialize_all_variables()

        max_allowed_loss = 0.1
        loss_val = max_allowed_loss
        initial_loss = None
        with self.test_session() as sess:
            sess.run(init)
            initial_loss = sess.run(loss)
            for i in range(50):
                loss_val, _ = sess.run([loss, optim])
                # print "i: %d loss: %f" % (i, loss_val)

        # Sanity check the initial loss was larger.
        self.assertGreater(initial_loss, max_allowed_loss)

        # Loss after training should be small.
        self.assertLess(loss_val, max_allowed_loss)

        # Loss should be at least two orders of magnitude better
        # than before training.
        self.assertLess(loss_val/initial_loss, 0.01)

if __name__ == '__main__':
    tf.test.main()

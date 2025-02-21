const express = require('express');
const multer = require('multer');
const auth = require('../middleware/auth');
const RabbitMQConnection = require('../service/rabbitmq');

require("dotenv").config();

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });
const rabbitmq = new RabbitMQConnection(process.env.RABBIMQ_URL);

router.post('/gen-ques', auth, upload.single("file"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded." });
  }

  try {
    // Won't connect again, if connection is already established, same connection is used
    await rabbitmq.connect();
    const uploadSuccess = await rabbitmq.publishFileToQueue(req.file, process.env.RABBITMQ_FILE_QUEUE_NAME);

    if (!uploadSuccess) {
      res.status(500).json({ error: "Internal server error." });
      return;
    }

    res.status(200).json({ message: "File in queue!" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Internal server error." });
  }
});

module.exports = router;
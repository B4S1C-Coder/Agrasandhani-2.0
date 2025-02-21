const amqp = require("amqplib");
const dotenv = require("dotenv");

dotenv.config();

const MAX_RETRIES = process.env.MAX_RABBITMQ_CON_RETRY;
const RETRY_DELAY = process.env.RABBITMQ_CON_RETRY_DELAY;

class RabbitMQConnection {
  constructor(url = process.env.RABBITMQ_URL) {
    this.url = url;
    this.connection = null;
    this.channel = null;
  }

  async connect(retryCount = 0) {
    try {
      if (!this.connection) {
        this.connection = await amqp.connect(this.url);

        this.connection.on("error", (err) => {
          console.log(`[ ERROR ] Error connecting to RabbitMQ: ${err}`);
          this.connection = null;
          this.channel = null;
        });

        this.connection.on("close", () => {
          console.log("RabbitMQ connection closed.");
          this.connection = null;
          this.channel = null;
        })

        console.log("Connected to RabbitMQ");
      }

      if (!this.channel) {
        this.channel = await this.connection.createChannel();
        console.log("Channel Created successfully");
      }

      return this.channel;
    }
    catch (error) {
      console.log(`Unable to connect to RabbitMQ: ${error.message}`);

      if (retryCount < MAX_RETRIES) {
        console.log(`Retrying connection in ${RETRY_DELAY/1000} seconds... (Attempt ${retryCount + 1}/${MAX_RETRIES})`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return this.connect(retryCount + 1);
      } else {
        console.log("[ FATAL-ERROR ] Failed to connect to RabbitMQ.");
        throw new Error("Failed to connect to RabbitMQ.");
      }

    }
  }

  async getChannel() {
    if (!this.channel) {
      return this.connect();
    } else {
      return this.channel;
    }
  }

  async closeConnection() {
    try {
      if (this.channel) {
        await this.channel.close();
        this.channel = null;
      }

      if (this.connection) {
        await this.connection.close();
        this.connection = null;
      }
    } catch (err) {
      console.warn("Error closing connection.");
    }
  }

  async publishMessage(message, queue, options={ durable: true }) {
    try {
      const channel = await this.getChannel();
      await channel.assertQueue(queue, options);

      const messageBuf = Buffer.from(
        typeof message === 'string' ? message : JSON.stringify(message)
      );

      const result = channel.sendToQueue(queue, messageBuf);
      console.log('Posted to queue.');
      return result;
    }
    catch (error) {
      console.warn(`Error posting message: ${error}`);
      return null;
    }
  }

  async publishFileToQueue(file, queue, options={ durable: true }) {
    try {
      const channel = await this.getChannel();
      await channel.assertQueue(queue, options);

      const result = channel.sendToQueue(queue, Buffer.from(file.buffer), {
        contentType: file.mimetype,
        headers: { filename: file.originalname },
      });

      console.log(`File posted to RabbitMQ: ${file.originalname}`);
      return result;
    }
    catch (error) {
      console.warn(`Error posting file: ${error}`);
      return null;
    }
  }
}

module.exports = RabbitMQConnection;
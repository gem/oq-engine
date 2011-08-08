package org.gem.log;

import org.junit.Ignore;

import java.io.IOException;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.ConfirmListener;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Consumer;
import com.rabbitmq.client.FlowListener;
import com.rabbitmq.client.GetResponse;
import com.rabbitmq.client.Method;
import com.rabbitmq.client.ReturnListener;
import com.rabbitmq.client.ShutdownListener;
import com.rabbitmq.client.ShutdownSignalException;

@Ignore
public class DummyChannel implements Channel {
    public class Entry {
        String exchange;
        String routingKey;
        AMQP.BasicProperties properties;
        String body;
    }

    public List<Entry> entries = new ArrayList<Entry>();

    private static void unimplemented() throws UnsupportedOperationException {
        throw new UnsupportedOperationException("Not implemented");
    }

    // ShutdownNotifier methods
    @Override
    public void addShutdownListener(ShutdownListener listener) {
        unimplemented();
    }

    @Override
    public void removeShutdownListener(ShutdownListener listener) {
        unimplemented();
    }

    @Override
    public ShutdownSignalException getCloseReason() {
        unimplemented();

        return null;
    }

    @Override
    public void notifyListeners() {
        unimplemented();
    }

    @Override
    public boolean isOpen() {
        unimplemented();

        return true;
    }

    // Channel methods
    @Override
    public int getChannelNumber() {
        unimplemented();

        return 0;
    }

    @Override
    public Connection getConnection() {
        unimplemented();

        return null;
    }

    @Override
    public void close() throws IOException {
        unimplemented();
    }

    @Override
    public void close(int closeCode, String closeMessage) throws IOException {
        unimplemented();
    }

    @Override
    public void abort() throws IOException {
        unimplemented();
    }

    @Override
    public void abort(int closeCode, String closeMessage) throws IOException {
        unimplemented();
    }

    @Override
    public AMQP.Channel.FlowOk flow(boolean active) throws java.io.IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Channel.FlowOk getFlow() {
        unimplemented();

        return null;
    }

    @Override
    public ReturnListener getReturnListener() {
        unimplemented();

        return null;
    }

    @Override
    public FlowListener getFlowListener() {
        unimplemented();

        return null;
    }

    @Override
    public Consumer getDefaultConsumer() {
        unimplemented();

        return null;
    }

    @Override
    public ConfirmListener getConfirmListener() {
        unimplemented();

        return null;
    }

    @Override
    public void basicNack(long deliveryTag, boolean multiple, boolean requeue) {
        unimplemented();
    }

    @Override
    public void basicReject(long deliveryTag, boolean requeue) throws java.io.IOException {
        unimplemented();
    }

    @Override
    public void basicQos(int prefetchSize, int prefetchCount, boolean global) throws IOException {
        unimplemented();
    }

    @Override
    public void basicQos(int prefetchCount) throws IOException {
        unimplemented();
    }

    @Override
    public AMQP.Basic.RecoverOk basicRecover() {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Basic.RecoverOk basicRecover(boolean requeue) {
        unimplemented();

        return null;
    }

    @Override
    public void basicRecoverAsync(boolean requeue) {
        unimplemented();
    }

    @Override
    public void basicPublish(String exchange, String routingKey, AMQP.BasicProperties props, byte[] body) throws IOException {
        Entry entry = new Entry();

        entry.exchange = exchange;
        entry.routingKey = routingKey;
        entry.properties = props;
        entry.body = new String(body);

        entries.add(entry);
    }

    @Override
    public void basicPublish(String exchange, String routingKey, boolean mandatory, boolean immediate, AMQP.BasicProperties props, byte[] body)
            throws IOException {
        unimplemented();
    }

    @Override
    public AMQP.Exchange.DeleteOk exchangeDelete(String exchange) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeclareOk exchangeDeclare(String exchange, String type) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeleteOk exchangeDelete(String exchange, boolean ifUnused) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeclareOk exchangeDeclare(String exchange, String type, boolean durable) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeclareOk exchangeDeclare(String exchange, String type, boolean passive, boolean durable, boolean autoDelete,
                                       Map<String, Object> arguments) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeclareOk exchangeDeclare(String exchange, String type, boolean durable, boolean autoDelete,
                                       Map<String, Object> arguments) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.DeclareOk exchangeDeclarePassive(String exchange) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.BindOk exchangeBind(java.lang.String destination, java.lang.String source, java.lang.String routingKey) {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.BindOk exchangeBind(java.lang.String destination, java.lang.String source, java.lang.String routingKey, java.util.Map<java.lang.String,java.lang.Object> arguments) {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.UnbindOk exchangeUnbind(java.lang.String destination, java.lang.String source, java.lang.String routingKey) {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Exchange.UnbindOk exchangeUnbind(java.lang.String destination, java.lang.String source, java.lang.String routingKey, java.util.Map<java.lang.String,java.lang.Object> arguments) {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.DeclareOk queueDeclare() throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.DeclareOk queueDeclare(String queue, boolean durable, boolean exclusive, boolean autoDelete,
                                 Map<String, Object> arguments) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.DeclareOk queueDeclarePassive(String queue) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.DeleteOk queueDelete(String queue) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.DeleteOk queueDelete(String queue, boolean ifUnused, boolean ifEmpty) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.BindOk queueBind(String queue, String exchange, String routingKey) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.BindOk queueBind(String queue, String exchange, String routingKey, Map<String, Object> arguments) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.UnbindOk queueUnbind(String queue, String exchange, String routingKey) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.UnbindOk queueUnbind(String queue, String exchange, String routingKey, Map<String, Object> arguments) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Queue.PurgeOk queuePurge(String queue) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public GetResponse basicGet(String queue, boolean noAck) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public void basicAck(long deliveryTag, boolean multiple) throws IOException {
        unimplemented();
    }

    @Override
    public String basicConsume(String queue, Consumer callback) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public String basicConsume(String queue, boolean noAck, Consumer callback) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public String basicConsume(String queue, boolean noAck, String consumerTag, Consumer callback) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public String basicConsume(String queue, boolean noAck, String consumerTag, boolean noLocal, boolean exclusive, Map<String, Object> arguments, Consumer callback) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public void basicCancel(String consumerTag) throws IOException {
        unimplemented();
    }

    @Override
    public AMQP.Tx.SelectOk txSelect() throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Tx.CommitOk txCommit() throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Tx.RollbackOk txRollback() throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public AMQP.Confirm.SelectOk confirmSelect() throws java.io.IOException {
        unimplemented();

        return null;
    }

    @Override
    public long getNextPublishSeqNo() {
        unimplemented();

        return 0;
    }

    @Override
    public void asyncRpc(Method method) throws IOException {
        unimplemented();
    }

    @Override
    public Method rpc(Method method) throws IOException {
        unimplemented();

        return null;
    }

    @Override
    public void setDefaultConsumer(Consumer consumer) {
        unimplemented();
    }

    @Override
    public void	setFlowListener(FlowListener listener) {
        unimplemented();
    }

    @Override
    public void	setConfirmListener(ConfirmListener listener) {
        unimplemented();
    }

    @Override
    public void setReturnListener(ReturnListener listener) {
        unimplemented();
    }
}

class DummyAppender extends AMQPAppender {
    @Override
    protected Channel getChannel() {
        if (channel == null)
            channel = new DummyChannel();

        return channel;
    }

    @Override
    protected Connection getConnection() {
        return null;
    }
}

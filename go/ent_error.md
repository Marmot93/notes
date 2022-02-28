### 起因
早上发现服务器崩了
### 排查
1. 发现异步任务的 worker 把内存吃满了，然后发现docker没有限制内存使用，就先把内存限制加上
2. 发现调用参与活动的接口会固定出问题，导致docker OOM 重启，但是订单都是正常的，只有通知消息不对。
3. 开始定位，发现通知消息的sql没有问题，是把sql的结果映射到model上出现问题了
4. 开了一个 profile 来跟踪，然后发现了是 newColumnMap 似乎有死循环，把内存打满了。
5. 然后看ent的源码，发现是 user.merchant.user.merchant... 无限循环了
6. 然后想办法先终止了 user.merchant 之后的解析

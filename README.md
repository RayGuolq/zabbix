# 介绍如何整合zabbix(3.2版本)到自己项目

首先要查看文档了解以下名词，在zabbix 服务器中的含义，可以结合web页面配置练习
- host：相当于一个主机（可以当作一个监控的主体）
- host group：主机组
- template：模板，为了方便配置host
- user group：用户组

## 代码模块介绍

### zabbixserver
- zabbixserver 是本人自己写的一个服务，目前版本 1.0
- 使用 tornado 暴露 rest api接口
- 调用者将数据post给该服务
- 服务再通过zabbix_sender将数据发到 zabbix 服务器上

### sms-script
- sms-script 是一个短信脚本
- 将此短信脚本集成到 zabbix 服务器
- zabbix 在触发triger规则后，可以通过短信方式通知用户

### python
- python/zabbix 是一个集成了 zabbix服务器api 的功能组件
- 将该组件引入到自己项目中，就可以自动化创建 zabbix服务配置（host，template，host group, user group）

>写在最后作为提醒，以上所有都是基于 zabbix3.2版本进行的整合，如果遇到问题请以官方文档为准 [zabbix document](https://www.zabbix.com/documentation)
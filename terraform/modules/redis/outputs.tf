output "redis_endpoint" {
  description = "Redis cluster endpoint with redis:// protocol"
  value       = "redis://${aws_elasticache_cluster.redis_cluster_dev.cache_nodes[0].address}:${aws_elasticache_cluster.redis_cluster_dev.cache_nodes[0].port}/0"
}

output "redis_address" {
  description = "Redis cluster primary endpoint address"
  value       = aws_elasticache_cluster.redis_cluster_dev.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_cluster.redis_cluster_dev.cache_nodes[0].port
}

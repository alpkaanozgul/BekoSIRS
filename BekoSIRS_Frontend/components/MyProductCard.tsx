import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { getImageUrl } from '../services/api';

interface Product {
  id: number;
  name: string;
  brand: string;
  price: string;
  image: string;
  category: {
    id: number;
    name: string;
  } | null;
  status: string;
  description: string;
}

interface MyProductCardProps {
  product: Product;
  onPress?: () => void;
}

const MyProductCard: React.FC<MyProductCardProps> = ({ product, onPress }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_stock':
        return '#10B981';
      case 'delivered':
        return '#3B82F6';
      case 'out_of_stock':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'in_stock':
        return 'Stokta';
      case 'delivered':
        return 'Teslim Edildi';
      case 'out_of_stock':
        return 'Stok Yok';
      default:
        return 'Bilinmiyor';
    }
  };

  return (
    <TouchableOpacity
      style={styles.card}
      activeOpacity={0.7}
      onPress={onPress}
    >
      {/* Product Image */}
      <View style={styles.imageContainer}>
        {product.image ? (
          <Image
            source={{ uri: getImageUrl(product.image) || '' }}
            style={styles.productImage}
            resizeMode="cover"
          />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>📦</Text>
          </View>
        )}

        {/* Status Badge */}
        <View
          style={[
            styles.statusBadge,
            { backgroundColor: getStatusColor(product.status) },
          ]}
        >
          <Text style={styles.statusText}>{getStatusText(product.status)}</Text>
        </View>
      </View>

      {/* Product Info */}
      <View style={styles.productInfo}>
        {/* Category */}
        {product.category && (
          <View style={styles.categoryContainer}>
            <Text style={styles.categoryIcon}>🏷️</Text>
            <Text style={styles.categoryText}>{product.category.name}</Text>
          </View>
        )}

        {/* Product Name */}
        <Text style={styles.productName} numberOfLines={2}>
          {product.name}
        </Text>

        {/* Brand */}
        {product.brand && (
          <Text style={styles.brandText}>Marka: {product.brand}</Text>
        )}

        {/* Price */}
        {product.price && (
          <View style={styles.priceContainer}>
            <Text style={styles.priceText}>{product.price}₺</Text>
            <View style={styles.priceBadge}>
              <Text style={styles.priceBadgeText}>KDV Dahil</Text>
            </View>
          </View>
        )}

        {/* Description */}
        {product.description && (
          <Text style={styles.descriptionText} numberOfLines={2}>
            {product.description}
          </Text>
        )}

        {/* Action Button */}
        <TouchableOpacity style={styles.detailButton}>
          <Text style={styles.detailButtonText}>Detayları Gör</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginBottom: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    height: 200,
    backgroundColor: '#F3F4F6',
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#E5E7EB',
  },
  placeholderText: {
    fontSize: 48,
  },
  statusBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  productInfo: {
    padding: 16,
  },
  categoryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  categoryText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  productName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
    lineHeight: 24,
  },
  brandText: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  priceText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000000',
    marginRight: 8,
  },
  priceBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  priceBadgeText: {
    fontSize: 10,
    color: '#6B7280',
    fontWeight: '600',
  },
  descriptionText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 16,
  },
  detailButton: {
    backgroundColor: '#000000',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  detailButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default MyProductCard;
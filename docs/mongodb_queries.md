# MongoDB Queries & Aggregation Pipelines Guide

This document contains key MongoDB queries and aggregation pipelines implemented in `MovieRec-BDA`.

---

## 1. Basic CRUD Operations

### Find Movies by Genre
```javascript
db.movies.find({ genres: "Comedy" }, { _id: 0, movieId: 1, title: 1, genres: 1 }).limit(5);
```

### Find Ratings Greater Than or Equal to 4.0
```javascript
db.ratings.find({ rating: { $gte: 4.0 } }, { _id: 0, userId: 1, movieId: 1, rating: 1 }).limit(5);
```

---

## 2. Advanced Aggregation Pipelines

### Pipeline 1: Most Rated Movies
Computes total rating volume and average score per movie.
```javascript
db.ratings.aggregate([
  {
    $group: {
      _id: "$movieId",
      rating_count: { $sum: 1 },
      average_rating: { $avg: "$rating" }
    }
  },
  { $sort: { rating_count: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "movies",
      localField: "_id",
      foreignField: "movieId",
      as: "movie_info"
    }
  },
  { $unwind: "$movie_info" },
  {
    $project: {
      movieId: "$_id",
      title: "$movie_info.title",
      genres: "$movie_info.genres",
      rating_count: 1,
      average_rating: { $round: ["$average_rating", 2] },
      _id: 0
    }
  }
]);
```

### Pipeline 2: Genre Distribution (Movies Count Per Genre)
Unwinds the `genres` array to count distinct titles under each genre category.
```javascript
db.movies.aggregate([
  { $unwind: "$genres" },
  {
    $group: {
      _id: "$genres",
      movie_count: { $sum: 1 }
    }
  },
  { $sort: { movie_count: -1 } },
  {
    $project: {
      genre: "$_id",
      movie_count: 1,
      _id: 0
    }
  }
]);
```

### Pipeline 3: Rating Value Distribution
Groups all ratings by star value (0.5 to 5.0) to generate histogram frequency data.
```javascript
db.ratings.aggregate([
  {
    $group: {
      _id: "$rating",
      count: { $sum: 1 }
    }
  },
  { $sort: { _id: 1 } },
  {
    $project: {
      rating: "$_id",
      count: 1,
      _id: 0
    }
  }
]);
```

### Pipeline 4: Highest Rated Movies with Rating Count Filter
Finds movies with highest average rating having at least 50 user ratings.
```javascript
db.ratings.aggregate([
  {
    $group: {
      _id: "$movieId",
      rating_count: { $sum: 1 },
      average_rating: { $avg: "$rating" }
    }
  },
  { $match: { rating_count: { $gte: 50 } } },
  { $sort: { average_rating: -1, rating_count: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "movies",
      localField: "_id",
      foreignField: "movieId",
      as: "movie_info"
    }
  },
  { $unwind: "$movie_info" },
  {
    $project: {
      movieId: "$_id",
      title: "$movie_info.title",
      average_rating: { $round: ["$average_rating", 2] },
      rating_count: 1,
      _id: 0
    }
  }
]);
```

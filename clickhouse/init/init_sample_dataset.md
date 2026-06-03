## MySQL
```shell
git clone https://github.com/datacharmer/test_db.git
mysql --commands -u root -p < employees.sql
mysql --commands -u root -p < employees_partitioned.sql

```

## MongoDB
```shell
git clone https://github.com/neelabalan/mongodb-sample-dataset.git
mongoimport --db sample_mflix --collection movies --file sample_mflix/movies.json --authenticationDatabase admin -u root -p <YOUR_PASSOWRD>
mongoimport --db sample_mflix --collection comments --file sample_mflix/comments.json --authenticationDatabase admin -u root -p <YOUR_PASSOWRD>
mongoimport --db sample_mflix --collection users --file sample_mflix/users.json --authenticationDatabase admin -u root -p <YOUR_PASSOWRD>

mongosh -u root -p
> use sample_mflix
> db.setProfilingLevel( 1, { slowms: 10 } );
> db.movies.find({title: /Star/});  -- 无索引模糊查询, 正则扫描全表
> db.movies.find({year: {$gte: 1980, $lte: 2020}});
> db.movies.aggregate([
    {
        $match: {
            year: {
                $gte: 1980
            }
        }
    },
    {
        $group: {
            _id: "$rated",
            count: {
                $sum: 1
            }
        }
    }
])
> db.comments.aggregate([
    {
        $lookup: {
            from: "movies",
            localField: "movie_id",
            foreignField: "_id",
            as: "movie"
        }
    }
])
> db.system.profile.countDocuments()
```
批量制造慢查询:
```javascript
for (let i = 0; i < 1000; i++) {

  db.movies.find({
    title: /Star/
  }).toArray()

  db.movies.find({
    year: {
      $gte: 1980
    }
  }).sort({
    tomatoes: -1
  }).toArray()

}
```
查看 profiler
```javascript
db.system.profile.find()
.sort({
  ts: -1
})
.limit(5)
.pretty()
```

